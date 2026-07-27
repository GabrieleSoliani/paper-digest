"""
Scarica i paper più recenti da arXiv per le categorie in config.yaml.
Usa l'API Atom pubblica di arXiv (nessuna API key necessaria).
Docs: https://info.arxiv.org/help/api/user-manual.html
"""
import time
import feedparser
import yaml
from pathlib import Path

ARXIV_API = "http://export.arxiv.org/api/query"
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def fetch_category(category: str, max_results: int) -> list[dict]:
    """Interroga l'API arXiv per una singola categoria, ordinando per data di submission."""
    query_url = (
        f"{ARXIV_API}?search_query=cat:{category}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )
    feed = feedparser.parse(query_url)

    papers = []
    for entry in feed.entries:
        papers.append({
            "id": entry.get("id", ""),
            "title": " ".join(entry.get("title", "").split()),
            "summary": " ".join(entry.get("summary", "").split()),
            "authors": [a.get("name", "") for a in entry.get("authors", [])],
            "published": entry.get("published", ""),
            "updated": entry.get("updated", ""),
            "link": entry.get("link", ""),
            "category": category,
            "source": "arxiv",
        })
    return papers


def fetch_all(config: dict) -> list[dict]:
    all_papers = []
    for cat in config["arxiv_categories"]:
        print(f"[arxiv] fetching category {cat}...")
        try:
            papers = fetch_category(cat, config["arxiv_max_results_per_category"])
            print(f"[arxiv]   -> {len(papers)} papers")
            all_papers.extend(papers)
        except Exception as e:
            print(f"[arxiv] ERROR fetching {cat}: {e}")
        # arXiv chiede di non martellare l'API: piccola pausa tra le richieste
        time.sleep(3)
    return all_papers


if __name__ == "__main__":
    import json
    cfg = load_config()
    result = fetch_all(cfg)
    out_path = Path(__file__).parent.parent / "data" / "raw_arxiv.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Salvati {len(result)} paper grezzi in {out_path}")
