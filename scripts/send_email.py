"""
Invia un'email con i paper nuovi (non ancora visti in run precedenti).
Usa SMTP (es. Gmail con App Password) tramite variabili d'ambiente/secrets:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL
Se non ci sono paper nuovi, non invia nulla (evita spam inutile).
"""
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).parent.parent


def build_email_html(papers: list[dict]) -> str:
    if not papers:
        return ""
    rows = []
    for p in papers:
        authors = ", ".join(p.get("authors", [])[:3])
        badge = "🤗 HF" if p["source"] == "huggingface" else f"arXiv/{p.get('category','')}"
        rows.append(f"""
        <tr><td style="padding:14px 0;border-bottom:1px solid #333;">
          <div style="font-size:11px;color:#6ea8fe;">{badge}</div>
          <a href="{p['link']}" style="font-size:16px;font-weight:600;color:#fff;text-decoration:none;">{p['title']}</a>
          <div style="font-size:12px;color:#999;margin:4px 0;">{authors}</div>
          <div style="font-size:13px;color:#ccc;">{p.get('summary','')[:280]}...</div>
        </td></tr>""")

    return f"""<html><body style="background:#0f1115;color:#eee;font-family:sans-serif;padding:20px;">
    <h2>📡 Paper Digest — {len(papers)} novità</h2>
    <table width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table>
    </body></html>"""


def send(html: str):
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📡 Il tuo Paper Digest settimanale"
    msg["From"] = user
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, recipient, msg.as_string())


if __name__ == "__main__":
    new_papers_path = ROOT / "data" / "new_papers.json"
    papers = json.loads(new_papers_path.read_text()) if new_papers_path.exists() else []

    if not papers:
        print("Nessun paper nuovo: email non inviata.")
    else:
        html = build_email_html(papers)
        send(html)
        print(f"Email inviata con {len(papers)} paper nuovi.")
