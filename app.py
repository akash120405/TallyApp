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
RECOMMENDATION_THRESHOLD = 4999


def build_recommendations():
    """Return practical savings suggestions for higher-spend ledgers."""
    subscriptions = sorted(
        tools.memory.items(),
        key=lambda item: item[1]["cost"],
        reverse=True,
    )
    monthly_total = sum(data["cost"] for _, data in subscriptions)
    if monthly_total <= RECOMMENDATION_THRESHOLD:
        return []

    recommendations = []
    for name, data in subscriptions[:3]:
        monthly_saving = round(data["cost"], 2)
        recommendations.append({
            "title": f"Review {name}",
            "detail": (
                f"At ₹{monthly_saving:,.2f}/month, this is one of your "
                "largest recurring costs. Canceling or downgrading it could "
                "free up meaningful headroom."
            ),
            "monthly_saving": monthly_saving,
            "yearly_saving": round(monthly_saving * 12, 2),
        })

    return recommendations


def serialize_state():
    items = [
        {"name": name, "cost": data["cost"], "renewal_date": data["renewal_date"]}
        for name, data in tools.memory.items()
    ]
    monthly_total = sum(data["cost"] for data in tools.memory.values())
    recommendations = build_recommendations()
    recommendations_available = monthly_total > RECOMMENDATION_THRESHOLD
    return {
        "subscriptions": items,
        "monthly_total": round(monthly_total, 2),
        "yearly_total": round(monthly_total * 12, 2),
        "subscription_count": len(items),
        "average_cost": round(monthly_total / len(items), 2) if items else 0,
        "recommendation_threshold": RECOMMENDATION_THRESHOLD,
        "recommendations_available": recommendations_available,
        "recommendations": recommendations,
        "monthly_budget": tools.budget,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/subscriptions", methods=["GET"])
def list_subscriptions():
    return jsonify(serialize_state())


@app.route("/api/budget", methods=["PUT"])
def update_budget():
    data = request.get_json(force=True) or {}
    amount = data.get("amount")
    if amount in (None, ""):
        tools.budget = None
        return jsonify(serialize_state())

    try:
        tools.set_monthly_budget.invoke({"amount": amount})
    except (ValueError, TypeError):
        return jsonify({"error": "Budget must be a number greater than zero."}), 400
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
    tools.budget = None
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
