"""
preprocessor.py - Text Tokenizer and Preprocessor for the Mini Search Engine.

This module handles all text cleaning before it goes into the index or is used
as a search query:
  1. Lowercasing
  2. Removing punctuation / special characters
  3. Removing common English stop words
  4. Simple suffix-stripping stemming (Porter-style, no external library)
"""

import re
from typing import List

# ── Stop-word list ─────────────────────────────────────────────────────────────
# A common set of English function words that carry little meaning on their own.
# Keeping this inline means no NLTK or other NLP library is required.

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "it", "its", "be", "was",
    "are", "were", "been", "has", "have", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "not", "no", "nor", "so", "yet", "both", "either", "neither", "as",
    "up", "out", "about", "into", "than", "then", "that", "this", "these",
    "those", "which", "who", "whom", "what", "when", "where", "why", "how",
    "all", "each", "every", "any", "some", "such", "more", "most", "also",
    "over", "under", "again", "further", "once", "here", "there", "just",
    "too", "very", "own", "same", "other", "only", "even", "after",
    "before", "during", "while", "because", "although", "though", "since",
    "until", "unless", "between", "through", "i", "me", "my", "we", "our",
    "you", "your", "he", "him", "his", "she", "her", "they", "them",
    "their", "us", "s", "t",
}


# ── Stemmer ────────────────────────────────────────────────────────────────────

def _stem(word: str) -> str:
    """Apply simple suffix-stripping rules (Porter-style, step 1 only).

    This is a deliberately lightweight stemmer: just enough to merge common
    inflections (e.g. "running" → "run", "pages" → "page") without pulling
    in an external library.

    Parameters
    ----------
    word : str
        A single lowercase token with no punctuation.

    Returns
    -------
    str
        The stemmed version of the word.
    """
    # Nothing to stem if word is very short
    if len(word) <= 3:
        return word

    # Order matters: try longer suffixes before shorter ones.
    suffixes = [
        ("ational", "ate"),
        ("tional",  "tion"),
        ("enci",    "ence"),
        ("anci",    "ance"),
        ("izer",    "ize"),
        ("ising",   "ise"),
        ("izing",   "ize"),
        ("nesses",  "ness"),
        ("ness",    ""),
        ("ments",   "ment"),
        ("ment",    ""),
        ("ings",    "ing"),
        ("ing",     ""),
        ("edly",    ""),
        ("ingly",   ""),
        ("ies",     "y"),
        ("ied",     "y"),
        ("sses",    "ss"),
        ("tions",   "te"),
        ("tion",    "te"),
        ("ers",     "er"),
        ("ly",      ""),
        ("ed",      ""),
        ("er",      ""),
        ("es",      ""),
        ("s",       ""),
    ]

    for suffix, replacement in suffixes:
        if word.endswith(suffix):
            stem = word[: len(word) - len(suffix)] + replacement
            # Keep the stem only if it is still reasonably long
            if len(stem) >= 3:
                return stem

    return word


# ── Public API ─────────────────────────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Convert raw text into a list of cleaned, stemmed tokens.

    Processing pipeline:
      1. Lowercase everything.
      2. Replace any character that is not a letter or digit with a space.
      3. Split into individual words.
      4. Remove stop words and very short tokens (length < 2).
      5. Apply suffix-stripping stemmer.

    Parameters
    ----------
    text : str
        Any raw text string (e.g. a web page's body text or a search query).

    Returns
    -------
    List[str]
        Ordered list of cleaned tokens.  May be empty if all tokens were
        stop words or too short.
    """
    if not text:
        return []

    # Step 1 – lowercase
    text = text.lower()

    # Step 2 – keep only letters and digits; turn everything else into spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Step 3 – split on whitespace
    words = text.split()

    # Steps 4 & 5 – filter and stem
    tokens: List[str] = []
    for word in words:
        if len(word) < 2:
            continue
        if word in STOP_WORDS:
            continue
        tokens.append(_stem(word))

    return tokens
