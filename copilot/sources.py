"""Read web pages for the source ledger, and check that a quote really appears on a page.

Two jobs (Rule 2: code decides what is verified, not the model):

    fetch_text(url)            the page's readable text (no scripts or styles)
    quote_in_text(quote, text) True if the quote appears in that text, ignoring differences
                               in whitespace, case, curly quotes, and invisible characters

Command line, used by the brief skill to read a page and copy exact quotes from it:

    python copilot/sources.py fetch <url>

Standard library only (Rule 5).
"""

import argparse
import http.client
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

# Some sites refuse requests that don't look like they come from a browser.
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT_SECONDS = 10
MAX_BYTES = 5_000_000  # stop reading after about 5 MB so one huge file can't stall a run
MAX_QUOTE_WORDS = 25  # SPEC.md: longer quotes are marked Unverified by check.py

# Text inside these tags is never shown to a reader, so it is never part of the page text.
SKIP_TAGS = {"script", "style", "noscript", "template"}

# These tags start a new line. Inline tags (a, b, strong, em, span) add nothing, so a sentence
# split across a link or bold text comes out as one sentence.
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "td", "th", "title", "tr", "ul",
}

# Curly quotes and primes become straight quotes before comparing.
QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
})

# Characters you can't see but that break a plain text search: zero-width space,
# zero-width non-joiner and joiner, word joiner, byte order mark, and soft hyphen.
INVISIBLE_MAP = str.maketrans(dict.fromkeys("​‌‍⁠﻿­"))


class FetchError(Exception):
    """The page did not load. The message says why, in plain English."""


def fetch_html(url: str, timeout: float = TIMEOUT_SECONDS) -> str:
    """Download a page and return it as a string. Raises FetchError if it doesn't load."""
    # urllib can also open file:// paths, which would read files on the user's computer.
    if urllib.parse.urlsplit(url).scheme.lower() not in ("http", "https"):
        raise FetchError(f"page did not load: only http and https links can be read, got {url!r}")

    request = urllib.request.Request(url, headers={
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if not (content_type.startswith("text/") or content_type == "application/xhtml+xml"):
                raise FetchError(f"page did not load: it is not a web page ({content_type})")
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read(MAX_BYTES)
    except urllib.error.HTTPError as error:
        # HTTPError must come before URLError because it is a kind of URLError.
        hint = " (the site may block scripts)" if error.code in (401, 403, 429) else ""
        raise FetchError(f"page did not load: HTTP {error.code} {error.reason}{hint}") from error
    except TimeoutError as error:
        raise FetchError(f"page did not load: timed out after {timeout} seconds") from error
    except urllib.error.URLError as error:
        # A timeout while connecting arrives wrapped inside a URLError.
        if isinstance(error.reason, TimeoutError):
            raise FetchError(f"page did not load: timed out after {timeout} seconds") from error
        raise FetchError(f"page did not load: {error.reason}") from error
    except (OSError, http.client.HTTPException, ValueError) as error:
        raise FetchError(f"page did not load: {error}") from error

    try:
        return body.decode(charset, errors="replace")
    except LookupError:  # the page named a character set Python doesn't know
        return body.decode("utf-8", errors="replace")


class _TextExtractor(HTMLParser):
    """Collects the text a reader would see, skipping scripts and styles."""

    def __init__(self):
        super().__init__(convert_charrefs=True)  # turns &amp; &nbsp; &rsquo; into characters
        self.parts = []
        self.skip_depth = 0  # above 0 while inside a <script>, <style>, and so on

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """The readable text of an HTML page, one block (heading, paragraph, list item) per line."""
    extractor = _TextExtractor()
    extractor.feed(html)
    extractor.close()
    text = "".join(extractor.parts)
    # Tidy each line's spacing and drop blank lines, so the output is easy to read.
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def fetch_text(url: str, timeout: float = TIMEOUT_SECONDS) -> str:
    """Download a page and return its readable text. Raises FetchError if it doesn't load."""
    return html_to_text(fetch_html(url, timeout=timeout))


def normalize(text: str) -> str:
    """Straighten curly quotes, drop invisible characters, ignore case, collapse whitespace.

    Nothing else is loosened (dashes and punctuation must still match exactly).
    """
    text = text.translate(QUOTE_MAP).translate(INVISIBLE_MAP).casefold()
    # split() with no argument splits on any whitespace, including non-breaking spaces.
    return " ".join(text.split())


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote appears in the page text after normalizing both."""
    needle = normalize(quote)
    if not needle:
        return False  # an empty quote would "match" every page
    return needle in normalize(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read web pages for a market brief.")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="print the readable text of a web page")
    fetch.add_argument("url")
    args = parser.parse_args(argv)

    # The Windows console can't print every character by default (curly quotes, accents),
    # so print UTF-8 instead of crashing partway through a page.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    try:
        text = fetch_text(args.url)
    except FetchError as error:
        print(error, file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
