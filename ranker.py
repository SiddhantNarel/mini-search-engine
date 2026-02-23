"""
ranker.py - TF-IDF Ranking for the Mini Search Engine.

TF-IDF (Term Frequency – Inverse Document Frequency) is the classic
information-retrieval scoring function.  It rewards documents that:
  • contain a query term *often* (high TF), and
  • contain a term that is *rare* across all documents (high IDF).

Formulas used here:
  TF  = (occurrences of term in doc) / (total tokens in doc)
  IDF = log( (total documents + 1) / (documents containing term + 1) ) + 1
          ↑ the "+1" smoothing avoids division-by-zero and log(0)

  Score(doc, query) = Σ  TF(term, doc) × IDF(term)
                      term ∈ query ∩ doc
"""

import math
from typing import Dict, List, Tuple, Any


def compute_tfidf_scores(
    query_tokens: List[str],
    index: Dict[str, Dict[str, List[int]]],
    doc_freq: Dict[str, int],
    documents: Dict[str, Dict[str, Any]],
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """Score every document that contains at least one query token.

    Parameters
    ----------
    query_tokens : list of str
        Pre-processed query terms (output of ``preprocessor.tokenize``).
    index : dict
        Inverted index: ``{term: {doc_id: [positions]}}``.
    doc_freq : dict
        Document-frequency mapping: ``{term: df}``.
    documents : dict
        Document metadata: ``{doc_id: {title, url, snippet, length}}``.
    top_k : int
        Maximum number of results to return.

    Returns
    -------
    list of (doc_id, score) tuples
        Sorted by score in descending order, limited to *top_k* entries.
    """
    total_docs = len(documents)

    # Accumulate TF-IDF scores across all query terms
    scores: Dict[str, float] = {}

    for term in query_tokens:
        if term not in index:
            # Term not in any document – skip it
            continue

        # IDF with "+1" smoothing so rare terms don't explode
        df  = doc_freq.get(term, 0)
        idf = math.log((total_docs + 1) / (df + 1)) + 1

        # Iterate over every document that contains this term
        for doc_id, positions in index[term].items():
            doc_meta = documents.get(doc_id)
            if doc_meta is None:
                continue

            doc_length = doc_meta.get("length", 1) or 1   # avoid div-by-zero
            tf         = len(positions) / doc_length
            tfidf      = tf * idf

            scores[doc_id] = scores.get(doc_id, 0.0) + tfidf

    # Sort by score descending, return at most top_k results
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
