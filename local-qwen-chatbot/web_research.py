from __future__ import annotations

import html
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser


DEFAULT_USER_AGENT = "LocalQwenTripPlanner/1.0"


@dataclass(frozen=True)
class WebPage:
    url: str
    title: str
    text: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_tag: str | None = None
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_tag = tag
        if tag == "title":
            self._in_title = True
        if tag in {"p", "br", "li", "h1", "h2", "h3", "tr"}:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == self._skip_tag:
            self._skip_tag = None
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_tag:
            return
        text = html.unescape(data).strip()
        if not text:
            return
        if self._in_title:
            self._title_parts.append(text)
        self._text_parts.append(text)

    @property
    def title(self) -> str:
        return clean_text(" ".join(self._title_parts)) or "Untitled page"

    @property
    def text(self) -> str:
        return clean_text(" ".join(self._text_parts))


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def extract_text_from_html(html_text: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html_text)
    return parser.title, parser.text


def extract_urls(raw_text: str) -> list[str]:
    candidates = re.findall(r"https?://[^\s<>()\"']+", raw_text)
    urls: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        url = candidate.rstrip(".,;]")
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls


def fetch_page(url: str, timeout_seconds: float = 12, max_chars: int = 6000) -> WebPage:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(800_000)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc

    if "pdf" in content_type.lower():
        raise RuntimeError(f"Skipping PDF URL for web crawl: {url}")

    html_text = raw.decode("utf-8", errors="replace")
    title, text = extract_text_from_html(html_text)
    if not text:
        raise RuntimeError(f"No readable text found at {url}")
    return WebPage(url=url, title=title, text=text[:max_chars])


def search_duckduckgo(query: str, max_results: int = 4) -> list[str]:
    encoded = urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        f"https://duckduckgo.com/html/?{encoded}",
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            html_text = response.read(400_000).decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Web search failed: {exc}") from exc

    urls: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r'href="([^"]+)"', html_text):
        href = html.unescape(match.group(1))
        parsed = urllib.parse.urlparse(href)
        target = href
        if parsed.path == "/l/":
            query_values = urllib.parse.parse_qs(parsed.query)
            target = query_values.get("uddg", [""])[0]
        if not target.startswith("http"):
            continue
        if "duckduckgo.com" in urllib.parse.urlparse(target).netloc:
            continue
        if target not in seen:
            urls.append(target)
            seen.add(target)
        if len(urls) >= max_results:
            break
    return urls


def research_web(
    query: str,
    urls_text: str = "",
    use_search: bool = True,
    max_pages: int = 4,
) -> tuple[list[WebPage], list[str]]:
    urls = extract_urls(urls_text)
    warnings: list[str] = []

    if use_search and query.strip():
        try:
            urls.extend(search_duckduckgo(query, max_results=max_pages))
        except RuntimeError as exc:
            warnings.append(str(exc))

    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            unique_urls.append(url)
            seen.add(url)

    pages: list[WebPage] = []
    for url in unique_urls[:max_pages]:
        try:
            pages.append(fetch_page(url))
        except RuntimeError as exc:
            warnings.append(str(exc))
    return pages, warnings
