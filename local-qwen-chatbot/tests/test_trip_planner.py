from trip_planner import TripRequest, build_search_query, build_trip_messages
from web_research import WebPage


def test_build_search_query_contains_trip_details():
    request = TripRequest(
        destination="Kyoto",
        dates="4 days in November",
        interests="temples and food",
    )

    query = build_search_query(request)

    assert "Kyoto" in query
    assert "4 days in November" in query
    assert "temples and food" in query


def test_build_trip_messages_include_sources_and_citation_instruction():
    request = TripRequest(destination="Paris", dates="3 days")
    pages = [
        WebPage(
            url="https://example.com/paris",
            title="Paris Guide",
            text="The Louvre is a major museum.",
        )
    ]

    messages = build_trip_messages(request, pages)

    assert messages[0]["role"] == "system"
    assert "cite sources" in messages[0]["content"].lower()
    assert "Paris" in messages[1]["content"]
    assert "[WEB 1: Paris Guide]" in messages[1]["content"]
    assert "The Louvre is a major museum." in messages[1]["content"]
