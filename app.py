"""
app.py - Flask Web UI for the Mini Search Engine.

Routes:
  GET  /            → Homepage with search bar
  GET  /search      → Search results page  (?q=<query>)
  GET  /crawl       → Form to start a new crawl
  POST /crawl       → Trigger a crawl and index the results
  GET  /api/stats   → JSON stats about the current index (bonus endpoint)
"""

import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify

from search_engine import SearchEngine
from crawler import Crawler
from indexer import Indexer
from config import MAX_CRAWL_DEPTH, MAX_PAGES, TOP_K_RESULTS, INDEX_FILE

# ── App setup ──────────────────────────────────────────────────────────────────

app = Flask(__name__)

# A single SearchEngine instance is shared across all requests.
# It is re-created after a successful crawl so the new index is picked up.
engine = SearchEngine()

# Track whether a crawl is currently in progress (simple flag – good enough for
# a single-user dev tool; not suitable for multi-user production deployments).
crawl_in_progress = False


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the homepage with the search bar."""
    stats = engine.index_stats()
    return render_template("index.html", stats=stats)


@app.route("/search")
def search():
    """Handle a search query and render the results page.

    Query parameters:
        q (str): The search query string.
    """
    query = request.args.get("q", "").strip()
    results = []
    elapsed = 0.0

    if query:
        import time
        start   = time.time()
        results = engine.search(query, top_k=TOP_K_RESULTS)
        elapsed = round(time.time() - start, 4)

    return render_template(
        "results.html",
        query=query,
        results=results,
        elapsed=elapsed,
        result_count=len(results),
    )


@app.route("/crawl", methods=["GET", "POST"])
def crawl():
    """GET: show the crawl form.  POST: start a crawl in a background thread."""
    global crawl_in_progress, engine

    message = None
    error   = None

    if request.method == "POST":
        seed_url  = request.form.get("seed_url", "").strip()
        max_depth = int(request.form.get("max_depth", MAX_CRAWL_DEPTH))
        max_pages = int(request.form.get("max_pages", MAX_PAGES))

        if not seed_url:
            error = "Please enter a seed URL."
        elif crawl_in_progress:
            error = "A crawl is already running. Please wait for it to finish."
        else:
            # Run the crawl in a background thread so the browser doesn't time out
            def run_crawl():
                global crawl_in_progress, engine
                crawl_in_progress = True
                try:
                    crawler = Crawler(
                        seed_url=seed_url,
                        max_depth=max_depth,
                        max_pages=max_pages,
                    )
                    pages = crawler.crawl()

                    # Build and save a new index from the freshly crawled pages
                    indexer = Indexer()
                    indexer.build_from_crawled_data(pages)
                    indexer.save(INDEX_FILE)

                    # Hot-reload the search engine so queries use the new index
                    engine = SearchEngine()
                finally:
                    crawl_in_progress = False

            thread = threading.Thread(target=run_crawl, daemon=True)
            thread.start()
            message = (
                f"Crawl started for {seed_url} "
                f"(max_depth={max_depth}, max_pages={max_pages}). "
                "This runs in the background — search results will update once it finishes."
            )

    return render_template(
        "crawl.html",
        message=message,
        error=error,
        crawl_in_progress=crawl_in_progress,
        default_max_depth=MAX_CRAWL_DEPTH,
        default_max_pages=MAX_PAGES,
    )


@app.route("/api/stats")
def api_stats():
    """Return basic index statistics as JSON.

    Useful for checking the engine status without a full page load.
    """
    stats = engine.index_stats()
    stats["crawl_in_progress"] = crawl_in_progress
    return jsonify(stats)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Use debug=True only for local development. Set FLASK_DEBUG=0 in production.
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=5000)
