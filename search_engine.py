"""
search_engine.py - Search / Query Engine for the Mini Search Engine.

This module ties together all the other components:
  Preprocessor → Index lookup → TF-IDF ranking → Result formatting

Usage:
    engine = SearchEngine()
    results = engine.search("python web crawling")
    for r in results:
        print(r["title"], r["score"])
"""

import os
from typing import List, Dict, Any

from config import INDEX_FILE, SAMPLE_INDEX_FILE, TOP_K_RESULTS
from preprocessor import tokenize
from indexer import Indexer
from ranker import compute_tfidf_scores


class SearchEngine:
    """High-level search interface that loads an index and answers queries."""

    def __init__(self) -> None:
        self.indexer = Indexer()
        self._load_best_available_index()

    # ── Index management ───────────────────────────────────────────────────────

    def _load_best_available_index(self) -> None:
        """Load the main index if it exists, otherwise fall back to sample data.

        This means the search engine works out of the box even before the user
        has crawled anything – it just uses the bundled sample index.
        """
        if os.path.exists(INDEX_FILE):
            self.indexer.load(INDEX_FILE)
        elif os.path.exists(SAMPLE_INDEX_FILE):
            print("[SearchEngine] No main index found – loading sample index.")
            self.indexer.load(SAMPLE_INDEX_FILE)
        else:
            print("[SearchEngine] Warning: no index file found. "
                  "Run a crawl first or add data/sample_index.json.")

    def reload_index(self) -> None:
        """Reload the index from disk (useful after a fresh crawl)."""
        self.indexer = Indexer()
        self._load_best_available_index()

    # ── Querying ───────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
    ) -> List[Dict[str, Any]]:
        """Search the index and return ranked results.

        Parameters
        ----------
        query : str
            The raw search query entered by the user.
        top_k : int
            Maximum number of results to return.

        Returns
        -------
        list of dict
            Each result dict contains:
              - ``title``   : page title
              - ``url``     : page URL
              - ``snippet`` : short text excerpt
              - ``score``   : TF-IDF relevance score (float)
              - ``doc_id``  : internal document identifier
        """
        if not query.strip():
            return []

        # Step 1 – clean the query the same way we cleaned the documents
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Step 2 – rank matching documents using TF-IDF
        ranked = compute_tfidf_scores(
            query_tokens=query_tokens,
            index=self.indexer.index,
            doc_freq=self.indexer.doc_freq,
            documents=self.indexer.documents,
            top_k=top_k,
        )

        # Step 3 – enrich results with metadata for display
        results: List[Dict[str, Any]] = []
        for doc_id, score in ranked:
            meta = self.indexer.documents.get(doc_id, {})
            results.append({
                "doc_id":  doc_id,
                "title":   meta.get("title",   "Untitled"),
                "url":     meta.get("url",     "#"),
                "snippet": meta.get("snippet", ""),
                "score":   round(score, 4),
            })

        return results

    # ── Stats helpers ──────────────────────────────────────────────────────────

    def index_stats(self) -> Dict[str, int]:
        """Return basic statistics about the current index.

        Returns
        -------
        dict with keys ``documents`` and ``terms``.
        """
        return {
            "documents": len(self.indexer.documents),
            "terms":     len(self.indexer.index),
        }
