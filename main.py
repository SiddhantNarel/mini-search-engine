"""
main.py - Command-Line Interface for the Mini Search Engine.

Usage examples:
  python main.py crawl https://en.wikipedia.org/wiki/Python_(programming_language)
  python main.py crawl https://example.com --depth 1 --pages 10
  python main.py search "machine learning"
  python main.py search "web crawler" --top 5
  python main.py runserver
  python main.py runserver --port 8080
  python main.py stats
"""

import argparse
import sys

from config import MAX_CRAWL_DEPTH, MAX_PAGES, TOP_K_RESULTS, INDEX_FILE


def cmd_crawl(args: argparse.Namespace) -> None:
    """Crawl a website and rebuild the search index.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments with attributes: url, depth, pages.
    """
    from crawler import Crawler
    from indexer import Indexer

    print(f"Starting crawl: {args.url}")
    crawler = Crawler(
        seed_url=args.url,
        max_depth=args.depth,
        max_pages=args.pages,
    )
    pages = crawler.crawl()

    if not pages:
        print("No pages were crawled. Check the URL and try again.")
        sys.exit(1)

    print(f"\nIndexing {len(pages)} pages…")
    indexer = Indexer()
    indexer.build_from_crawled_data(pages)
    indexer.save(INDEX_FILE)
    print("Done! You can now run:  python main.py search \"your query\"")


def cmd_search(args: argparse.Namespace) -> None:
    """Search the index and print ranked results to the terminal.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments with attributes: query (list of str), top (int).
    """
    from search_engine import SearchEngine

    query   = " ".join(args.query)
    engine  = SearchEngine()
    results = engine.search(query, top_k=args.top)

    if not results:
        print(f"No results found for: {query!r}")
        return

    print(f"\nTop {len(results)} result(s) for: {query!r}\n")
    print("-" * 70)

    for rank, result in enumerate(results, start=1):
        print(f"{rank}. {result['title']}")
        print(f"   URL:     {result['url']}")
        print(f"   Score:   {result['score']}")
        print(f"   Snippet: {result['snippet'][:120]}…")
        print()


def cmd_runserver(args: argparse.Namespace) -> None:
    """Start the Flask web server.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments with attribute: port (int).
    """
    from app import app
    print(f"Starting web server at http://localhost:{args.port}/")
    print("Press Ctrl-C to stop.\n")
    app.run(debug=False, port=args.port)


def cmd_stats(_args: argparse.Namespace) -> None:
    """Print basic statistics about the current index."""
    from search_engine import SearchEngine
    engine = SearchEngine()
    stats  = engine.index_stats()
    print(f"Documents indexed : {stats['documents']}")
    print(f"Unique terms      : {stats['terms']}")


# ── CLI definition ─────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Mini Search Engine — command-line interface",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── crawl ──────────────────────────────────────────────────────────────────
    p_crawl = sub.add_parser("crawl", help="Crawl a website and build the index")
    p_crawl.add_argument("url",                     help="Seed URL to start from")
    p_crawl.add_argument("--depth", "-d", type=int, default=MAX_CRAWL_DEPTH,
                         help=f"Maximum link depth (default: {MAX_CRAWL_DEPTH})")
    p_crawl.add_argument("--pages", "-p", type=int, default=MAX_PAGES,
                         help=f"Maximum pages to crawl (default: {MAX_PAGES})")
    p_crawl.set_defaults(func=cmd_crawl)

    # ── search ─────────────────────────────────────────────────────────────────
    p_search = sub.add_parser("search", help="Search the index")
    p_search.add_argument("query",  nargs="+",   help="Search query (can be multiple words)")
    p_search.add_argument("--top",  "-k", type=int, default=TOP_K_RESULTS,
                          help=f"Number of results to show (default: {TOP_K_RESULTS})")
    p_search.set_defaults(func=cmd_search)

    # ── runserver ──────────────────────────────────────────────────────────────
    p_server = sub.add_parser("runserver", help="Start the Flask web UI")
    p_server.add_argument("--port", type=int, default=5000,
                          help="Port to listen on (default: 5000)")
    p_server.set_defaults(func=cmd_runserver)

    # ── stats ──────────────────────────────────────────────────────────────────
    p_stats = sub.add_parser("stats", help="Show index statistics")
    p_stats.set_defaults(func=cmd_stats)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)
