# 📡 Paper Digest — dashboard + email automatica

Monitora automaticamente arXiv (cs.CV, cs.RO, cs.LG, cs.AI) e i Daily Papers di
Hugging Face, filtra per le tue keyword (SAM, DINO, VLA, anomaly detection, ecc.),
e produce:

1. una **dashboard web statica** sempre aggiornata (`docs/index.html`, pubblicabile
   gratis con GitHub Pages)
2. un'**email settimanale** con i soli paper *nuovi* rispetto all'ultima run

Tutto gira gratis su **GitHub Actions**, senza bisogno di un server o del tuo PC acceso.

---

## Setup (10 minuti)

### 1. Crea il repository
- Crea un nuovo repo su GitHub (può essere privato o pubblico)
- Carica tutti questi file mantenendo la struttura di cartelle

### 2. Attiva GitHub Pages
- Settings → Pages → Source: `Deploy from a branch`
- Branch: `main`, cartella: `/docs`
- Salva. Dopo la prima run del workflow, la dashboard sarà su
  `https://<tuo-utente>.github.io/<nome-repo>/`

### 3. Configura l'invio email (opzionale ma consigliato)
Vai su Settings → Secrets and variables → Actions → New repository secret,
e crea questi 5 secret:

| Nome | Valore (esempio con Gmail) |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | la tua email Gmail |
| `SMTP_PASSWORD` | una **App Password** (NON la password normale — vedi sotto) |
| `RECIPIENT_EMAIL` | dove vuoi ricevere il digest (può essere la stessa email) |

**Come creare una App Password Gmail:**
Account Google → Sicurezza → Verifica in due passaggi (deve essere attiva) →
"Password per le app" → generane una nuova, incollala in `SMTP_PASSWORD`.

Se preferisci un altro provider (Outlook, un dominio custom, SendGrid ecc.),
basta cambiare host/porta: la logica SMTP standard resta la stessa.

> Se non configuri i secret email, il workflow funzionerà lo stesso e
> aggiornerà solo la dashboard — semplicemente lo step email fallirà in modo
> innocuo (puoi anche rimuovere quello step dal file `.github/workflows/digest.yml`).

### 4. Personalizza le keyword
Apri `config.yaml` e modifica la lista `keywords` con i termini che ti interessano
(già precompilata con SAM, DINO, RoMa, VLA, anomaly detection, ecc. — aggiungine
quante ne vuoi).

### 5. Prova subito, senza aspettare lunedì
Vai su Actions → "Paper Digest" → **Run workflow** (pulsante in alto a destra):
lo lancia manualmente per verificare che tutto funzioni.

---

## Come modificare la frequenza

Nel file `.github/workflows/digest.yml`, la riga:
```yaml
- cron: "0 6 * * 1"
```
è in formato cron (minuto ora giorno-mese mese giorno-settimana), orario UTC.
Esempi:
- `"0 6 * * *"` → ogni giorno alle 06:00 UTC
- `"0 6 * * 1,4"` → lunedì e giovedì
- `"0 6 1 * *"` → il primo di ogni mese

---

## Struttura del progetto

```
paper-digest/
├── config.yaml              # keyword, categorie arXiv, soglie
├── requirements.txt
├── scripts/
│   ├── fetch_arxiv.py       # scarica da arXiv API
│   ├── fetch_hf_papers.py   # scarica da Hugging Face Daily Papers
│   ├── build_digest.py      # filtra, deduplica, rankizza, genera la dashboard HTML
│   └── send_email.py        # invia email con i soli paper nuovi
├── .github/workflows/
│   └── digest.yml           # orchestratore: schedule + esecuzione + commit + email
├── data/                    # stato persistente (committato automaticamente)
└── docs/                    # dashboard pubblicata via GitHub Pages
```

## Note tecniche

- **Deduplicazione**: un paper già mostrato in una run precedente non
  ricompare nell'email successiva (tracciato in `data/seen_ids.json`), ma
  resta visibile nella dashboard finché rientra nella finestra temporale
  configurata.
- **Ranking**: punteggio basato su numero di keyword matchate + bonus per
  paper già curati da Hugging Face + bonus per upvotes ricevuti su HF.
- **Endpoint Hugging Face**: `fetch_hf_papers.py` usa un endpoint pubblico
  non ufficiale; se in futuro HF lo cambia, è l'unico file da aggiornare.
- **Rate limiting arXiv**: lo script rispetta le linee guida arXiv con una
  pausa di 3s tra le richieste per categoria.
