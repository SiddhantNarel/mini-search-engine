# Mini Search Engine

A lightweight, fully-functional search engine built in Python as a 4th-year undergraduate project.  
It demonstrates core information-retrieval concepts: **web crawling**, **text preprocessing**, **inverted indexing**, and **TF-IDF ranking**, all wired up to a clean **Flask web interface**.

---

## Architecture

```
Web Crawler → Tokenizer/Preprocessor → Inverted Index Builder → TF-IDF Ranker → Flask Web UI
```

---

## Features

- 🕷 **Web Crawler** – BFS crawl within a single domain, respects `robots.txt`
- 🧹 **Text Preprocessor** – lowercasing, stop-word removal, suffix-stripping stemmer (no NLTK needed)
- 📚 **Inverted Index** – stores `{term: {doc_id: [positions]}}` with document-frequency counts
- 📊 **TF-IDF Ranking** – implemented from scratch (no sklearn)
- 🌐 **Flask Web UI** – search bar, results page, crawl-trigger form
- 💾 **Sample Index** – works out of the box with 15 pre-built Wikipedia documents
- 🖥 **CLI** – `crawl`, `search`, `runserver`, and `stats` commands

---

## Project Structure

```
mini-search-engine/
├── README.md
├── requirements.txt
├── .gitignore
├── config.py           ← all constants/settings
├── main.py             ← CLI entry point
├── crawler.py          ← web crawler
├── preprocessor.py     ← tokeniser + stemmer
├── indexer.py          ← inverted index builder
├── ranker.py           ← TF-IDF scoring
├── search_engine.py    ← ties everything together
├── app.py              ← Flask web application
├── templates/
│   ├── base.html
│   ├── index.html      ← homepage
│   ├── results.html    ← search results
│   └── crawl.html      ← crawl-trigger form
├── static/
│   └── style.css       ← custom CSS (no frameworks)
└── data/
    └── sample_index.json  ← pre-built sample index
```

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/SiddhantNarel/mini-search-engine.git
cd mini-search-engine

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Web UI (recommended)

```bash
python main.py runserver
# Then open http://localhost:5000 in your browser
```

### Command-line

```bash
# Search the built-in sample index
python main.py search "machine learning"
python main.py search "web crawler python" --top 5

# Crawl a website and rebuild the index
python main.py crawl https://en.wikipedia.org/wiki/Python_(programming_language)
python main.py crawl https://example.com --depth 1 --pages 10

# Show index statistics
python main.py stats
```

---

## How It Works

| Component | File | Description |
|-----------|------|-------------|
| Configuration | `config.py` | Central constants (depths, paths, limits) |
| Crawler | `crawler.py` | BFS over a domain, honours `robots.txt`, saves page JSON |
| Preprocessor | `preprocessor.py` | Lowercase → remove punctuation → stop words → stem |
| Indexer | `indexer.py` | Builds `{term → {doc_id → [positions]}}` + DF table |
| Ranker | `ranker.py` | TF-IDF: `TF × log((N+1)/(df+1)) + 1` per query term |
| Search Engine | `search_engine.py` | Loads index, preprocesses query, calls ranker |
| Web UI | `app.py` + `templates/` | Flask routes + Jinja2 templates |
| CLI | `main.py` | `argparse`-based command-line interface |

---

## Technologies Used

- **Python 3.8+**
- **Flask** – web framework
- **Requests** – HTTP client for the crawler
- **BeautifulSoup4 + lxml** – HTML parsing
- Standard library only for everything else (`re`, `json`, `math`, `urllib`, …)

---

## Possible Improvements / Future Work

- Phrase queries (`"exact phrase"`) using positional index information
- Boolean operators (`AND`, `OR`, `NOT`)
- PageRank-style link-graph scoring
- Persistent crawl queue (resume after interruption)
- Autocomplete via a trie data structure
- Pagination on the results page
- Docker container for easy deployment
