# Tally — a ledger for your subscriptions | Subscription Management Agent

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
  ₹500, renews on the 5th"* or *"I'm over my ₹5,000 budget, what should I
  cancel?"* — and the agent will call its tools and reply.
- Or skip the chat and use the quick-add row at the bottom of the ledger
  table to add an entry instantly, without going through the model.
- Set a monthly budget in the ledger panel to see a headroom bar (it's
  saved by the Flask app and restored when the ledger reloads). The clerk can
  also set it when you say something like *"Set my monthly budget to ₹5,000"*.
- "Clear the ledger" wipes all subscriptions and starts a fresh
  conversation with the agent.
- All totals and inputs use Indian rupees (₹).
- When monthly spending goes above ₹5,000, the **Recommendations** tab highlights
  the largest recurring costs and estimates monthly and yearly savings.
- Search the ledger or export its current entries as a CSV for budgeting.

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

## Tools Used
| Tool | What it does | Example request |
|---|---|---|
| `add_subscription()` | Adds a subscription record to the ledger. | “Add Netflix for ₹500 monthly.” |
| `remove_subscription()` | Removes a subscription record from the ledger. | “Remove Netflix.” |



                 TallyApp
                     │
                     ▼
               Natural Language
                     │
                     ▼
                    NLP
                     │
                     ▼
                    LLM
              (understands request)
                     │
                     ▼
                 LangChain
          (connects LLM with tools)
                     │
                     ▼
                 LangGraph
           (controls the workflow)
                     │
                     ▼
               Agentic AI
                     │
              ┌──────┴──────┐
              ▼             ▼
        Add subscription   Check budget

        <img width="732" height="673" alt="image" src="https://github.com/user-attachments/assets/c016906e-2285-4af0-a26c-f9d97ec2c3d8" />

              │             │
              └──────┬──────┘
                     ▼
                Final response
