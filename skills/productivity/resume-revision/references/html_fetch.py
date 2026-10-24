#!/usr/bin/env python3
"""
Fallback HTML-to-text fetcher for when the browser is unavailable.
Usage: python3 html_fetch.py <url>
"""

import sys
import urllib.request
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.skip_tags = {"script", "style", "noscript"}
        self.current_tags = []

    def handle_starttag(self, tag, attrs):
        self.current_tags.append(tag)
        if tag in self.skip_tags:
            self.skip = True

    def handle_endtag(self, tag):
        if self.current_tags and self.current_tags[-1] == tag:
            self.current_tags.pop()
        if tag in self.skip_tags:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            stripped = data.strip()
            if stripped:
                self.text.append(stripped)


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(html)
    return "\n".join(parser.text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 html_fetch.py <url>")
        sys.exit(1)
    print(fetch(sys.argv[1]))
