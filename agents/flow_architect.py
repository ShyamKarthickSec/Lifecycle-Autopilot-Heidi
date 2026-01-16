import json
from openai import OpenAI

from core.schemas import FlowSpec
from core.prompts import FLOW_ARCHITECT_SYSTEM


def _json_only(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
    return t.strip()


def run_flow_architect(
    *,
    client: OpenAI,
    model: str,
    goal: str,
    wedge_name: str,
    urgency: str,
) -> FlowSpec:
    prompt = {
        "goal": goal,
        "wedge_name": wedge_name,
        "urgency": urgency,
        "requirements": {
            "steps": 3,
            "channels": ["email", "sms", "in_app"],
            "default_timing": ["T+48h", "T+60h", "T+96h"],
        },
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.25,
        messages=[
            {"role": "system", "content": FLOW_ARCHITECT_SYSTEM},
            {"role": "user", "content": json.dumps(prompt, indent=2)},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(_json_only(content))
    return FlowSpec(**data)
