"""
config.py - Central configuration file for the Mini Search Engine.

All constants and settings are defined here so they can be easily changed
without touching other files.
"""

import os

# ── Crawling settings ──────────────────────────────────────────────────────────

# Maximum depth to follow links from the seed URL (0 = seed only)
MAX_CRAWL_DEPTH: int = 2

# Maximum number of pages to crawl in a single run (safety limit)
MAX_PAGES: int = 50

# Seconds to wait between requests (be polite to servers!)
CRAWL_DELAY: float = 1.0

# HTTP request timeout in seconds
REQUEST_TIMEOUT: int = 10

# User-Agent string sent with every request
USER_AGENT: str = "MiniSearchBot/1.0 (+https://github.com/example/mini-search-engine)"

# ── File paths ─────────────────────────────────────────────────────────────────

# Root directory of the project (same folder as this file)
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Directory where crawled pages and the index are stored
DATA_DIR: str = os.path.join(BASE_DIR, "data")

# Path to the main inverted index file
INDEX_FILE: str = os.path.join(DATA_DIR, "index.json")

# Path to the sample/pre-built index (used when no crawl has been done yet)
SAMPLE_INDEX_FILE: str = os.path.join(DATA_DIR, "sample_index.json")

# ── Search settings ────────────────────────────────────────────────────────────

# Default number of results to return for a query
TOP_K_RESULTS: int = 10

# Number of characters to show as a snippet in results
SNIPPET_LENGTH: int = 200
