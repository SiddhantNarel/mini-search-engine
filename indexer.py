"""
indexer.py - Inverted Index Builder for the Mini Search Engine.

An inverted index maps each unique term to the list of documents that contain
it, along with the positions of the term within each document.  This is the
core data structure that lets a search engine answer "which documents mention
term X?" in O(1) look-up time.

Index structure (stored in JSON):
{
  "index": {
    "<term>": {
      "<doc_id>": [<pos1>, <pos2>, ...]   ← positions of term in the doc
    }
  },
  "doc_freq": {
    "<term>": <number of docs containing term>
  },
  "documents": {
    "<doc_id>": {
      "title":   "<page title>",
      "url":     "<page URL>",
      "snippet": "<short excerpt>",
      "length":  <total token count>
    }
  }
}
"""

import json
import os
from typing import Dict, List, Any

from config import INDEX_FILE, DATA_DIR, SNIPPET_LENGTH
from preprocessor import tokenize


# ── Type aliases ───────────────────────────────────────────────────────────────

# Postings list: {doc_id: [position, ...]}
Postings = Dict[str, List[int]]

# Full inverted index: {term: postings}
InvertedIndex = Dict[str, Postings]

# Document metadata store: {doc_id: {title, url, snippet, length}}
Documents = Dict[str, Dict[str, Any]]


# ── Indexer class ──────────────────────────────────────────────────────────────

class Indexer:
    """Builds and manages the inverted index."""

    def __init__(self) -> None:
        # Main inverted index: term → {doc_id → [positions]}
        self.index: InvertedIndex = {}

        # Document frequency: term → number of documents containing it
        self.doc_freq: Dict[str, int] = {}

        # Document metadata
        self.documents: Documents = {}

    # ── Building ───────────────────────────────────────────────────────────────

    def add_document(self, doc_id: str, title: str, url: str, text: str) -> None:
        """Tokenize one document and add it to the index.

        Parameters
        ----------
        doc_id : str
            A unique identifier for this document (e.g. "doc_0").
        title : str
            The human-readable title of the page.
        url : str
            The URL where the page was found.
        text : str
            The full body text of the page.
        """
        tokens = tokenize(text)

        # Build a short snippet from the *original* text (before preprocessing)
        snippet = self._make_snippet(text)

        # Store metadata so we can display results without re-fetching pages
        self.documents[doc_id] = {
            "title":   title,
            "url":     url,
            "snippet": snippet,
            "length":  len(tokens),   # total tokens – used by TF calculation
        }

        # Record which terms appear at which positions
        # We also track which terms we've already seen in THIS document so that
        # doc_freq is only incremented once per document per term.
        seen_in_doc: set = set()

        for position, token in enumerate(tokens):
            # Ensure the term has an entry in the index
            if token not in self.index:
                self.index[token] = {}

            # Append position to this document's postings list
            if doc_id not in self.index[token]:
                self.index[token][doc_id] = []
            self.index[token][doc_id].append(position)

            # Update document frequency (once per doc per term)
            if token not in seen_in_doc:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1
                seen_in_doc.add(token)

    def build_from_crawled_data(self, crawled_pages: List[Dict[str, Any]]) -> None:
        """Build the index from a list of crawled page dictionaries.

        Each page dict should have keys: 'title', 'url', 'text'.

        Parameters
        ----------
        crawled_pages : list of dict
            Output from the crawler – one dict per page.
        """
        for i, page in enumerate(crawled_pages):
            doc_id = f"doc_{i}"
            self.add_document(
                doc_id=doc_id,
                title=page.get("title", "Untitled"),
                url=page.get("url", ""),
                text=page.get("text", ""),
            )
        print(f"[Indexer] Indexed {len(self.documents)} documents, "
              f"{len(self.index)} unique terms.")

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, filepath: str = INDEX_FILE) -> None:
        """Save the index to a JSON file on disk.

        Parameters
        ----------
        filepath : str
            Destination path for the JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "index":     self.index,
            "doc_freq":  self.doc_freq,
            "documents": self.documents,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[Indexer] Index saved to {filepath}")

    def load(self, filepath: str = INDEX_FILE) -> bool:
        """Load a previously saved index from a JSON file.

        Parameters
        ----------
        filepath : str
            Path to the JSON index file.

        Returns
        -------
        bool
            True if the file was loaded successfully, False otherwise.
        """
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.index     = data.get("index",     {})
            self.doc_freq  = data.get("doc_freq",  {})
            self.documents = data.get("documents", {})

            print(f"[Indexer] Loaded index from {filepath} "
                  f"({len(self.documents)} docs, {len(self.index)} terms).")
            return True

        except (json.JSONDecodeError, KeyError) as exc:
            print(f"[Indexer] Failed to load index: {exc}")
            return False

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_snippet(text: str, length: int = SNIPPET_LENGTH) -> str:
        """Return the first *length* characters of *text* as a plain snippet.

        Parameters
        ----------
        text : str
            Full page text.
        length : int
            Maximum number of characters in the snippet.

        Returns
        -------
        str
            Truncated text ending at a word boundary, with "…" appended when
            truncation occurred.
        """
        text = " ".join(text.split())   # normalise whitespace
        if len(text) <= length:
            return text

        # Try to cut at a space so we don't chop a word in half
        cut = text.rfind(" ", 0, length)
        if cut == -1:
            cut = length

        return text[:cut] + "…"
