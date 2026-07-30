from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from web_research import WebPage


TRIP_SYSTEM_PROMPT = (
    "You are a careful travel planning assistant. Use the provided web research "
    "as the main source of current information. Build practical itineraries, "
    "call out assumptions, cite sources like [WEB 1], and remind the user to "
    "verify prices, opening hours, visas, weather, and bookings before travel."
)


@dataclass(frozen=True)
class TripRequest:
    destination: str
    dates: str
    starting_city: str = ""
    travelers: str = "1 traveler"
    budget: str = "moderate"
    interests: str = ""
    pace: str = "balanced"
    notes: str = ""


def build_search_query(request: TripRequest) -> str:
    parts = [
        request.destination,
        "travel guide attractions hotels local transport food",
        request.dates,
        request.interests,
    ]
    return " ".join(part for part in parts if part.strip())


def build_web_context(pages: Iterable[WebPage], max_chars_per_page: int = 1800) -> str:
    sections: list[str] = []
    for index, page in enumerate(pages, start=1):
        text = page.text[:max_chars_per_page].strip()
        sections.append(
            f"[WEB {index}: {page.title}]\nURL: {page.url}\nEXTRACT:\n{text}"
        )
    return "\n\n".join(sections)


def build_trip_prompt(request: TripRequest, web_context: str) -> str:
    context = web_context or "No web pages were available. State that live research was not available."
    return f"""
Create an interactive vacation plan using the details and web research below.

TRIP DETAILS
- Destination: {request.destination}
- Dates or duration: {request.dates}
- Starting city: {request.starting_city or "not provided"}
- Travelers: {request.travelers}
- Budget: {request.budget}
- Interests: {request.interests or "not provided"}
- Pace: {request.pace}
- Extra notes: {request.notes or "none"}

WEB RESEARCH
{context}

RESPONSE FORMAT
1. Start with 2-3 clarifying assumptions if any details are missing.
2. Give a day-by-day itinerary.
3. Include food, transport and booking tips.
4. Include a budget-aware recommendation section.
5. Include a short checklist before travel.
6. Cite web sources with [WEB 1], [WEB 2], etc. when using researched facts.
""".strip()


def build_trip_messages(
    request: TripRequest,
    pages: Iterable[WebPage],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": TRIP_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_trip_prompt(request, build_web_context(pages)),
        },
    ]


def build_trip_follow_up_messages(
    history: Iterable[dict[str, str]],
    pages: Iterable[WebPage],
    follow_up: str,
    max_history_messages: int = 12,
) -> list[dict[str, str]]:
    source_context = build_web_context(pages, max_chars_per_page=1000)
    source_message = {
        "role": "system",
        "content": (
            f"{TRIP_SYSTEM_PROMPT}\n\nAvailable source context for follow-up:\n"
            f"{source_context or 'No web source context is available.'}"
        ),
    }
    return [
        source_message,
        *list(history)[-max_history_messages:],
        {"role": "user", "content": follow_up},
    ]
