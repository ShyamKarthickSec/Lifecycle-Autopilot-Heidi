import json
from openai import OpenAI

from core.schemas import CohortInsight
from core.prompts import COHORT_DETECTIVE_SYSTEM


def _json_only(text: str) -> str:
    # Strip fenced blocks if present
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
    return t.strip()


def run_cohort_detective(
    *,
    client: OpenAI,
    model: str,
    goal: str,
    wedge_name: str,
    wedge: str,
    cohort_size: int,
    dropoff_rate: str,
    total_users: int,
    urgency_hint: str,
) -> CohortInsight:
    user = {
        "goal": goal,
        "wedge": wedge,
        "wedge_name": wedge_name,
        "cohort_size": cohort_size,
        "dropoff_rate": dropoff_rate,
        "total_users": total_users,
        "urgency_hint": urgency_hint,
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": COHORT_DETECTIVE_SYSTEM},
            {"role": "user", "content": f"Input stats:\n{json.dumps(user, indent=2)}"},
        ],
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(_json_only(content))

    # enforce the computed cohort size/rate (trust data over model)
    data["size"] = int(cohort_size)
    data["dropoff_rate"] = dropoff_rate
    if "urgency" not in data:
        data["urgency"] = urgency_hint

    return CohortInsight(**data)
