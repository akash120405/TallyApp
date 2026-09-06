# Tally — a ledger for your subscriptions

A small web app around the Subscription Manager Agent: a Flask backend
wraps the original LangChain agent and tools, and a browser frontend
gives you a ledger view, a budget headroom bar, and a chat panel to
talk to the agent directly.

## What's inside

- `agent.py` / `tools.py` — the original agent and tools, with the API
  key moved out of the source and into `.env`, plus a `remove_subscription`
  tool so you can cancel things by name.
- `app.py` — Flask backend exposing:
  - `GET /api/subscriptions` — current ledger state
  - `POST /api/subscriptions` — add an entry directly (used by the quick-add form)
  - `DELETE /api/subscriptions/<name>` — remove an entry
  - `POST /api/chat` — send a message to the agent
  - `POST /api/reset` — clear the ledger and start a new conversation
- `templates/index.html`, `static/style.css`, `static/script.js` — the frontend.
- `.env` — already contains the API key you gave me.

## Run it locally

```bash
cd tally-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser.

## Using it

- Type naturally in the "Ask the clerk" panel — e.g. *"Add Netflix for
  $15, renews on the 5th"* or *"I'm over my $50 budget, what should I
  cancel?"* — and the agent will call its tools and reply.
- Or skip the chat and use the quick-add row at the bottom of the ledger
  table to add an entry instantly, without going through the model.
- Set a monthly budget in the ledger panel to see a headroom bar (it's
  stored in your browser only).
- "Clear the ledger" wipes all subscriptions and starts a fresh
  conversation with the agent.

## About the API key

Your NVIDIA NIM key is saved in `.env` (not committed to git — see
`.gitignore`) and is only read on the server side; the browser never
sees it. Since you shared it in plain text in our chat, it's worth
rotating it in the NVIDIA console if you'd rather it not linger
anywhere outside this file.

## Deploying somewhere other than your laptop

This is a stateful Flask app (the ledger lives in memory, not a
database), so the simplest hosts are ones that run a single
long-lived Python process — Render, Railway, Fly.io, or a small VPS.
Set `NVIDIA_API_KEY` as an environment variable on whichever platform
you pick instead of shipping the `.env` file.
