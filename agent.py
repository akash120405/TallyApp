"""
Subscription Manager Agent built with LangChain.
Utilizes ChatOpenAI, tool binding, and typed messages for a minimal agent loop.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from tools import add_subscription, remove_subscription, get_monthly_total

load_dotenv()

# Map tool names to their functions
TOOL_MAP = {
    t.name: t
    for t in [add_subscription, remove_subscription, get_monthly_total]
}

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

if not NVIDIA_API_KEY:
    raise RuntimeError(
        "NVIDIA_API_KEY is not set. Add it to a .env file "
        "(see .env.example) before starting the app."
    )

# NVIDIA LLM
llm = ChatOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
    model="openai/gpt-oss-20b",
    temperature=0.0,
    max_tokens=512
).bind_tools(list(TOOL_MAP.values()))


# Agent instructions
SYSTEM_PROMPT = (
    "You are a Subscription Manager Agent. "
    "Use `add_subscription` for new subscriptions, "
    "`remove_subscription` to cancel one, "
    "then `get_monthly_total` to inspect totals. "
    "If over budget, suggest what to cancel. "
    "Always give a short, concise response with monthly total, "
    "yearly total, and renewal reminders."
)


class SubscriptionAgent:

    def __init__(self):
        self.messages = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

    def run(self, user_goal: str):

        print(
            f"\n{'=' * 65}\n"
            f"[USER]: {user_goal}\n"
            f"{'=' * 65}"
        )

        # Add user's message
        self.messages.append(
            HumanMessage(content=user_goal)
        )

        while True:

            # Ask the LLM what to do
            msg = llm.invoke(self.messages)

            # Save LLM response
            self.messages.append(msg)

            # If there are no tools to call,
            # the model has produced its final answer
            if not msg.tool_calls:

                content = msg.content

                # Handle different content formats
                if isinstance(content, list):
                    content = "".join(
                        block.get("text", "")
                        if isinstance(block, dict)
                        else str(block)
                        for block in content
                    )

                safe_text = str(content or "").strip()

                print(
                    f"\n[AGENT RESPONSE]:\n"
                    f"{safe_text}\n"
                )

                return safe_text

            # Execute each requested tool
            for tc in msg.tool_calls:

                clean_name = (
                    tc["name"]
                    .split("<|")[0]
                    .split("(")[0]
                    .strip()
                )

                tool_func = TOOL_MAP.get(clean_name)

                if tool_func:

                    result = tool_func.invoke(tc["args"])

                else:

                    result = (
                        f"Error: Tool '{clean_name}' not found."
                    )

                print(
                    f" -> [TOOL CALL] "
                    f"{clean_name}({tc['args']}) => {result}"
                )

                # Send tool result back to the LLM
                self.messages.append(
                    ToolMessage(
                        tool_call_id=tc["id"],
                        content=str(result)
                    )
                )