from web_research import extract_text_from_html, extract_urls


def test_extract_text_from_html_skips_scripts_and_styles():
    title, text = extract_text_from_html(
        """
        <html>
          <head>
            <title>Travel Guide</title>
            <style>.hidden { display: none; }</style>
            <script>alert("ignore me")</script>
          </head>
          <body>
            <h1>Best places</h1>
            <p>Museum opens at 10 AM.</p>
          </body>
        </html>
        """
    )

    assert title == "Travel Guide"
    assert "Best places" in text
    assert "Museum opens at 10 AM." in text
    assert "ignore me" not in text


def test_extract_urls_deduplicates_and_trims_punctuation():
    urls = extract_urls(
        "Read https://example.com/a, then https://example.com/b. "
        "Again: https://example.com/a"
    )

    assert urls == ["https://example.com/a", "https://example.com/b"]
