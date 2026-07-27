"""
Unisce i paper scaricati da arXiv e Hugging Face, li filtra per keyword,
deduplica, rankizza e produce:
  - docs/index.html         -> dashboard completa (ultimi N giorni, sempre aggiornata)
  - data/new_papers.json    -> solo i paper MAI visti prima (per l'email)
  - data/seen_ids.json      -> stato persistente (committato nel repo)
"""
import json
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"


def load_json(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def keyword_score(text: str, keywords: list[str]) -> int:
    text_low = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_low)


def build():
    cfg = yaml.safe_load(open(ROOT / "config.yaml"))
    keywords = cfg["keywords"]

    arxiv_papers = load_json(DATA_DIR / "raw_arxiv.json", [])
    hf_papers = load_json(DATA_DIR / "raw_hf.json", [])
    seen_ids = set(load_json(DATA_DIR / "seen_ids.json", []))

    combined = []
    seen_titles = set()

    # arXiv: filtriamo per keyword (titolo o abstract)
    for p in arxiv_papers:
        text = f"{p['title']} {p['summary']}"
        score = keyword_score(text, keywords)
        if score == 0:
            continue
        norm = normalize_title(p["title"])
        if norm in seen_titles:
            continue
        seen_titles.add(norm)
        p["score"] = score + 1  # +1 base
        combined.append(p)

    # HF daily papers: già curati manualmente da HF, li includiamo sempre
    # ma diamo un bonus di score se matchano anche le nostre keyword
    for p in hf_papers:
        text = f"{p['title']} {p.get('summary', '')}"
        score = keyword_score(text, keywords)
        norm = normalize_title(p["title"])
        if norm in seen_titles:
            continue
        seen_titles.add(norm)
        p["score"] = score + 2 + min(p.get("upvotes", 0) / 10, 3)  # bonus curation + upvotes
        combined.append(p)

    # Ordina per score decrescente, poi per data più recente
    combined.sort(key=lambda p: (p["score"], p.get("published", "")), reverse=True)
    combined = combined[: cfg["max_papers_in_digest"]]

    # Nuovi paper mai visti prima (per l'email)
    new_papers = [p for p in combined if p["id"] not in seen_ids]

    # Aggiorna lo stato "visti"
    updated_seen = seen_ids | {p["id"] for p in combined}
    # Teniamo solo gli ultimi 2000 id per non far crescere il file all'infinito
    updated_seen = list(updated_seen)[-2000:]

    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "digest.json", "w") as f:
        json.dump(combined, f, indent=2)
    with open(DATA_DIR / "new_papers.json", "w") as f:
        json.dump(new_papers, f, indent=2)
    with open(DATA_DIR / "seen_ids.json", "w") as f:
        json.dump(updated_seen, f, indent=2)

    render_html(combined)
    print(f"Digest costruito: {len(combined)} paper totali, {len(new_papers)} nuovi.")
    return combined, new_papers


def render_html(papers: list[dict]):
    DOCS_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cards = []
    for p in papers:
        authors = ", ".join(p.get("authors", [])[:4])
        if len(p.get("authors", [])) > 4:
            authors += " et al."
        badge = "🤗 HF" if p["source"] == "huggingface" else f"arXiv · {p.get('category','')}"
        cards.append(f"""
        <article class="card">
          <div class="badge">{badge}</div>
          <h2><a href="{p['link']}" target="_blank" rel="noopener">{p['title']}</a></h2>
          <p class="authors">{authors}</p>
          <p class="summary">{p.get('summary','')[:320]}...</p>
          <div class="meta">score: {round(p['score'],1)} · {p.get('published','')[:10]}</div>
        </article>""")

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paper Digest — aggiornato {now}</title>
<style>
  :root {{
    --bg: #0f1115; --card: #171a21; --text: #e8e8ea; --muted: #9a9fa8;
    --accent: #6ea8fe; --border: #262b35;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1.2rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  header {{ max-width: 820px; margin: 0 auto 2rem; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
  .updated {{ color: var(--muted); font-size: 0.9rem; }}
  input#search {{
    width: 100%; max-width: 820px; display: block; margin: 1rem auto 2rem;
    padding: 0.7rem 1rem; border-radius: 8px; border: 1px solid var(--border);
    background: var(--card); color: var(--text); font-size: 1rem;
  }}
  .grid {{ max-width: 820px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }}
  .card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.1rem 1.3rem;
  }}
  .badge {{
    display: inline-block; font-size: 0.72rem; color: var(--accent);
    border: 1px solid var(--accent); border-radius: 999px; padding: 0.1rem 0.6rem;
    margin-bottom: 0.5rem;
  }}
  .card h2 {{ font-size: 1.05rem; margin: 0.2rem 0 0.4rem; line-height: 1.35; }}
  .card h2 a {{ color: var(--text); text-decoration: none; }}
  .card h2 a:hover {{ color: var(--accent); }}
  .authors {{ color: var(--muted); font-size: 0.85rem; margin: 0 0 0.5rem; }}
  .summary {{ font-size: 0.9rem; line-height: 1.5; color: #cfd2d8; margin: 0 0 0.5rem; }}
  .meta {{ font-size: 0.78rem; color: var(--muted); }}
</style>
</head>
<body>
  <header>
    <h1>📡 Il mio Paper Digest</h1>
    <p class="updated">Ultimo aggiornamento: {now} · {len(papers)} paper</p>
  </header>
  <input id="search" type="text" placeholder="Filtra per parola chiave (es. VLA, SAM, robot)...">
  <div class="grid" id="grid">
    {"".join(cards)}
  </div>
  <script>
    const input = document.getElementById('search');
    const cards = Array.from(document.querySelectorAll('.card'));
    input.addEventListener('input', () => {{
      const q = input.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.innerText.toLowerCase().includes(q) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    with open(DOCS_DIR / "index.html", "w") as f:
        f.write(html)


if __name__ == "__main__":
    build()
