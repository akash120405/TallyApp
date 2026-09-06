"""
Tools and Memory for Subscription Manager using LangChain @tool decorator.
Three tools: add_subscription(name, cost), remove_subscription(name), and
get_monthly_total(). Includes Group of 3 add-ons: renewal-date reminders
and yearly-cost view.
"""

from langchain_core.tools import tool

# Memory: Remembers all active subscriptions across turns
memory = {}

@tool
def add_subscription(name: str, cost: float, renewal_date: str = "1st of next month") -> str:
    """Add or update a subscription with its monthly cost and renewal date."""
    cost_val = float(str(cost).replace("$", "").strip())
    memory[name.strip()] = {
        "cost": cost_val,
        "renewal_date": str(renewal_date)
    }
    return f"Added '{name}' at ${cost_val:.2f}/month (Renewal Date: {renewal_date})."

@tool
def remove_subscription(name: str) -> str:
    """Cancel/remove an active subscription by name."""
    key = name.strip()
    if key in memory:
        del memory[key]
        return f"Removed '{key}'."
    for existing in list(memory.keys()):
        if existing.lower() == key.lower():
            del memory[existing]
            return f"Removed '{existing}'."
    return f"No subscription named '{key}' found."

@tool
def get_monthly_total() -> str:
    """Return all active subscriptions, monthly total, and yearly-cost view."""
    monthly_total = sum(item["cost"] for item in memory.values())
    yearly_total = monthly_total * 12
    return (
        f"Active Subscriptions: {memory} | "
        f"Monthly Total: ${monthly_total:.2f} | "
        f"Yearly Total: ${yearly_total:.2f}"
    )
