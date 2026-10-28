"""
Tools and Memory for Subscription Manager using LangChain @tool decorator.
Tools for managing subscriptions, the monthly budget, and spending totals.
"""

from langchain_core.tools import tool

# Memory: Remembers all active subscriptions across turns
memory = {}
budget = None

@tool
def add_subscription(name: str, cost: float, renewal_date: str = "1st of next month") -> str:
    """Add or update a subscription with its monthly cost and renewal date."""
    cost_val = float(str(cost).replace("$", "").replace("₹", "").replace("INR", "").strip())
    memory[name.strip()] = {
        "cost": cost_val,
        "renewal_date": str(renewal_date)
    }
    return f"Added '{name}' at ₹{cost_val:.2f}/month (Renewal Date: {renewal_date})."

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
        f"Monthly Total: ₹{monthly_total:.2f} | "
        f"Yearly Total: ₹{yearly_total:.2f}"
    )


@tool
def set_monthly_budget(amount: float | str) -> str:
    """Set or replace the monthly subscription budget in Indian rupees."""
    global budget
    amount_val = float(str(amount).replace("$", "").replace("₹", "").replace("INR", "").replace(",", "").strip())
    if amount_val <= 0:
        raise ValueError("Budget must be greater than zero.")
    budget = amount_val
    return f"Monthly budget set to ₹{amount_val:,.2f}."
