"""
Scarica i "Daily Papers" selezionati dalla community/staff di Hugging Face.
Endpoint pubblico non ufficiale: https://huggingface.co/api/daily_papers
Se HF cambia l'endpoint in futuro, questo è l'unico file da aggiornare.
"""
import json
import requests
from datetime import date, timedelta
from pathlib import Path

HF_API = "https://huggingface.co/api/daily_papers"


def fetch_days_back(days_back: int) -> list[dict]:
    all_papers = []
    seen_ids = set()

    for i in range(days_back):
        day = date.today() - timedelta(days=i)
        params = {"date": day.isoformat()}
        try:
            resp = requests.get(HF_API, params=params, timeout=20)
            resp.raise_for_status()
            items = resp.json()
        except Exception as e:
            print(f"[hf] ERROR per {day}: {e}")
            continue

        for item in items:
            paper = item.get("paper", item)
            paper_id = paper.get("id") or item.get("paper", {}).get("id")
            if not paper_id or paper_id in seen_ids:
                continue
            seen_ids.add(paper_id)
            all_papers.append({
                "id": paper_id,
                "title": paper.get("title", ""),
                "summary": paper.get("summary", ""),
                "authors": [a.get("name", "") for a in paper.get("authors", [])] if paper.get("authors") else [],
                "published": paper.get("publishedAt", day.isoformat()),
                "link": f"https://huggingface.co/papers/{paper_id}",
                "upvotes": item.get("upvotes", 0),
                "source": "huggingface",
            })
        print(f"[hf] {day}: {len(items)} paper trovati")

    return all_papers


if __name__ == "__main__":
    import yaml
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    result = fetch_days_back(cfg.get("hf_days_back", 7))
    out_path = Path(__file__).parent.parent / "data" / "raw_hf.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Salvati {len(result)} paper HF in {out_path}")
