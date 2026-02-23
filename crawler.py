"""
crawler.py - Web Crawler for the Mini Search Engine.

Crawls web pages starting from a seed URL, following links up to a given
depth, while:
  • Respecting robots.txt (via urllib.robotparser)
  • Staying within the same domain as the seed
  • Adding a polite delay between requests
  • Saving each page as a JSON file in data/

Usage (from Python):
    from crawler import Crawler
    c = Crawler(seed_url="https://example.com", max_depth=2, max_pages=20)
    pages = c.crawl()
"""

import json
import os
import re
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

from config import DATA_DIR, MAX_CRAWL_DEPTH, MAX_PAGES, CRAWL_DELAY, REQUEST_TIMEOUT, USER_AGENT


class Crawler:
    """Breadth-first web crawler that stays within a single domain."""

    def __init__(
        self,
        seed_url: str,
        max_depth: int = MAX_CRAWL_DEPTH,
        max_pages: int = MAX_PAGES,
        delay: float = CRAWL_DELAY,
    ) -> None:
        """Initialise the crawler.

        Parameters
        ----------
        seed_url : str
            The first URL to visit.
        max_depth : int
            How many link-hops away from the seed to follow.
        max_pages : int
            Hard cap on total pages fetched (safety limit).
        delay : float
            Seconds to sleep between HTTP requests.
        """
        self.seed_url   = seed_url
        self.max_depth  = max_depth
        self.max_pages  = max_pages
        self.delay      = delay

        # Derive the base domain so we stay on the same site
        parsed         = urlparse(seed_url)
        self.base_url  = f"{parsed.scheme}://{parsed.netloc}"
        self.domain    = parsed.netloc

        # Tracking state
        self.visited:  set = set()
        self.pages:    List[Dict[str, Any]] = []

        # HTTP session (reuses TCP connections)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        # robots.txt parser
        self.robot_parser = urllib.robotparser.RobotFileParser()
        robots_url        = f"{self.base_url}/robots.txt"
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
        except Exception:
            # If we can't read robots.txt, assume everything is allowed
            pass

    # ── Public interface ───────────────────────────────────────────────────────

    def crawl(self) -> List[Dict[str, Any]]:
        """Run the crawl and return a list of page dictionaries.

        Each dictionary has the keys:
          - ``url``   : the page URL
          - ``title`` : the <title> element text
          - ``text``  : all visible body text

        Returns
        -------
        list of dict
            One entry per successfully crawled page.
        """
        print(f"[Crawler] Starting crawl from {self.seed_url} "
              f"(max_depth={self.max_depth}, max_pages={self.max_pages})")

        # Queue contains (url, depth) pairs
        queue: List[tuple] = [(self.seed_url, 0)]

        while queue and len(self.pages) < self.max_pages:
            url, depth = queue.pop(0)

            if url in self.visited:
                continue
            if depth > self.max_depth:
                continue
            if not self._is_allowed(url):
                print(f"[Crawler] Blocked by robots.txt: {url}")
                continue

            self.visited.add(url)
            page = self._fetch_page(url)

            if page is None:
                continue

            self.pages.append(page)
            print(f"[Crawler] [{len(self.pages)}/{self.max_pages}] "
                  f"depth={depth}  {url}")

            # Discover links and add them to the queue
            if depth < self.max_depth:
                links = self._extract_links(page.get("html", ""), url)
                for link in links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))

            # Polite delay between requests
            time.sleep(self.delay)

        print(f"[Crawler] Finished. Crawled {len(self.pages)} pages.")
        self._save_pages()
        return self.pages

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Download *url* and return a page dict, or None on failure.

        Parameters
        ----------
        url : str
            The URL to fetch.

        Returns
        -------
        dict or None
        """
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Only process HTML pages
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None

            soup  = BeautifulSoup(response.text, "lxml")
            title = self._extract_title(soup)
            text  = self._extract_text(soup)

            return {
                "url":   url,
                "title": title,
                "text":  text,
                "html":  response.text,   # kept temporarily for link extraction
            }

        except requests.exceptions.RequestException as exc:
            print(f"[Crawler] Error fetching {url}: {exc}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Return the text of the first <title> element, or 'Untitled'."""
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else "Untitled"

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Return all visible text from the page, with boilerplate removed.

        We strip <script>, <style>, and <nav> tags because they add noise.
        """
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        return " ".join(soup.get_text(separator=" ").split())

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Parse all <a href="..."> links and return same-domain absolute URLs.

        Parameters
        ----------
        html : str
            Raw HTML of the page.
        base_url : str
            The URL the HTML was fetched from (used to resolve relative links).

        Returns
        -------
        list of str
            Absolute URLs belonging to the same domain as the seed.
        """
        soup  = BeautifulSoup(html, "lxml")
        links = []

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()

            # Skip non-page links
            if href.startswith(("#", "mailto:", "javascript:")):
                continue

            # Resolve relative URLs
            absolute = urljoin(base_url, href)

            # Strip query strings and fragments to reduce duplicates
            parsed = urlparse(absolute)
            clean  = parsed._replace(query="", fragment="").geturl()

            # Only follow links within the same domain
            if urlparse(clean).netloc == self.domain:
                links.append(clean)

        return links

    def _is_allowed(self, url: str) -> bool:
        """Return True if robots.txt permits fetching *url*.

        Parameters
        ----------
        url : str
            The URL to check.
        """
        try:
            return self.robot_parser.can_fetch(USER_AGENT, url)
        except Exception:
            return True   # Assume allowed on any parser error

    def _save_pages(self) -> None:
        """Write all crawled pages to individual JSON files in DATA_DIR."""
        os.makedirs(DATA_DIR, exist_ok=True)

        for i, page in enumerate(self.pages):
            # Don't persist the raw HTML in saved files (saves disk space)
            saveable = {k: v for k, v in page.items() if k != "html"}
            filepath = os.path.join(DATA_DIR, f"page_{i}.json")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(saveable, f, indent=2, ensure_ascii=False)

        print(f"[Crawler] Saved {len(self.pages)} page files to {DATA_DIR}/")
