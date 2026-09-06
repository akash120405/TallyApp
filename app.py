"""
Flask backend for the Tally subscription ledger.
Serves the frontend and exposes a small API around the LangChain agent
and its tools, so the UI can both chat with the agent and make quick
direct edits to the ledger.
"""

from flask import Flask, request, jsonify, render_template

from agent import SubscriptionAgent
import tools

app = Flask(__name__)

agent = SubscriptionAgent()


def serialize_state():
    items = [
        {"name": name, "cost": data["cost"], "renewal_date": data["renewal_date"]}
        for name, data in tools.memory.items()
    ]
    monthly_total = sum(data["cost"] for data in tools.memory.values())
    return {
        "subscriptions": items,
        "monthly_total": round(monthly_total, 2),
        "yearly_total": round(monthly_total * 12, 2),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/subscriptions", methods=["GET"])
def list_subscriptions():
    return jsonify(serialize_state())


@app.route("/api/subscriptions", methods=["POST"])
def add_subscription_direct():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    cost = data.get("cost")
    renewal_date = (data.get("renewal_date") or "1st of next month").strip()

    if not name or cost in (None, ""):
        return jsonify({"error": "Name and cost are required."}), 400

    try:
        tools.add_subscription.invoke({"name": name, "cost": cost, "renewal_date": renewal_date})
    except (ValueError, TypeError):
        return jsonify({"error": "Cost must be a number."}), 400

    return jsonify(serialize_state())


@app.route("/api/subscriptions/<path:name>", methods=["DELETE"])
def remove_subscription_direct(name):
    tools.remove_subscription.invoke({"name": name})
    return jsonify(serialize_state())


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400

    try:
        reply = agent.run(message)
    except Exception as exc:  # surfaces API/auth errors to the UI instead of a 500 page
        return jsonify({"error": str(exc)}), 502

    return jsonify({"reply": reply or "", "state": serialize_state()})


@app.route("/api/reset", methods=["POST"])
def reset():
    global agent
    tools.memory.clear()
    agent = SubscriptionAgent()
    return jsonify(serialize_state())


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
