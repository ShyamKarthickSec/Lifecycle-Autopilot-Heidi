import json
from openai import OpenAI

from core.schemas import MessagesBundle, FlowStep
from core.prompts import COPYWRITER_SYSTEM


def _json_only(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
    return t.strip()


def _normalize_messages(data: dict, wedge_name: str) -> dict:
    """
    Some model responses occasionally omit title/notes for sms/in_app.
    We coerce a minimal structure so Pydantic validation passes and the UI renders.
    """

    def ensure_channel(key: str, fallback_title: str, fallback_notes: str):
        channel = data.get(key, {}) or {}
        channel.setdefault("title", fallback_title)
        channel.setdefault("notes", fallback_notes)
        channel.setdefault("variants", [])
        # Ensure variants are a list of dicts; skip malformed entries.
        if not isinstance(channel["variants"], list):
            channel["variants"] = []
        cleaned = []
        for v in channel["variants"]:
            if not isinstance(v, dict):
                continue
            # Preserve known fields; ignore extras.
            cleaned.append(
                {
                    "tone": v.get("tone", "clear"),
                    "cta": v.get("cta", "Take the next step"),
                    "text": v.get("text", ""),
                }
            )
        channel["variants"] = cleaned
        if not channel["variants"]:
            channel["variants"] = [
                {
                    "tone": "clear",
                    "cta": "Take the next step",
                    "text": "Quick nudge to keep care moving.",
                }
            ]
        data[key] = channel

    ensure_channel(
        "email",
        fallback_title=f"{wedge_name} — activation email",
        fallback_notes="Brief email to prompt next action.",
    )
    ensure_channel(
        "sms",
        fallback_title=f"{wedge_name} — quick SMS",
        fallback_notes="Short SMS reminder; under 240 characters.",
    )
    ensure_channel(
        "in_app",
        fallback_title=f"{wedge_name} — in-app nudge",
        fallback_notes="Concise in-app card; under 280 characters.",
    )

    return data


def run_copywriter(
    *,
    client: OpenAI,
    model: str,
    goal: str,
    wedge_name: str,
    trigger: str,
    sequence: list[FlowStep],
) -> MessagesBundle:
    seq = [s.model_dump() for s in sequence]
    user = {
        "goal": goal,
        "wedge_name": wedge_name,
        "trigger": trigger,
        "sequence": seq,
        "constraints": {
            "variants_per_channel": 3,
            "sms_max_chars": 240,
            "in_app_max_chars": 280,
        },
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.6,
        messages=[
            {"role": "system", "content": COPYWRITER_SYSTEM},
            {"role": "user", "content": json.dumps(user, indent=2)},
        ],
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(_json_only(content))
    data = _normalize_messages(data, wedge_name=wedge_name)
    return MessagesBundle(**data)
