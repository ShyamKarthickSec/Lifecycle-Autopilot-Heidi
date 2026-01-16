import json
import re
from typing import Tuple

from openai import OpenAI

from core.schemas import MessagesBundle, QAGate, CohortInsight, FlowSpec, ExplainBundle
from core.prompts import EVALUATOR_SYSTEM, EXPLAIN_SYSTEM
from agents.copywriter import run_copywriter


RISKY_PATTERNS = [
    r"\bcure\b",
    r"\bdiagnos(e|is)\b",
    r"\bguarantee\b",
    r"\bimprove patient outcomes\b",
    r"\bmedical advice\b",
    r"\breplaces (your|the) clinician\b",
]


def _json_only(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
    return t.strip()


def _rule_based_flags(messages: MessagesBundle) -> list[str]:
    flags = []
    text_blob = json.dumps(messages.model_dump()).lower()
    for pat in RISKY_PATTERNS:
        if re.search(pat, text_blob):
            flags.append(f"Risky phrase detected: /{pat}/")
    # simple spam signal
    if text_blob.count("!") > 6:
        flags.append("Too many exclamation marks (spammy tone).")
    return flags


def run_evaluator(
    *,
    client: OpenAI,
    model: str,
    wedge_name: str,
    messages: MessagesBundle,
) -> QAGate:
    base_flags = _rule_based_flags(messages)

    payload = {
        "wedge_name": wedge_name,
        "messages": messages.model_dump(),
        "known_flags": base_flags,
        "scoring_rubric": {
            "clarity": "clear, short, actionable",
            "spam_risk": "no pushy language, no excessive punctuation",
            "brand_tone": "calm, confident, time-saving workflow",
            "healthcare_safety": "no outcomes promises, no medical advice",
        },
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(_json_only(content))

    # Merge flags
    flags = list(dict.fromkeys((data.get("flags") or []) + base_flags))
    score = float(data.get("score", 0.5))

    # Penalize if rule-based flags exist
    if base_flags:
        score = max(0.0, score - 0.15)

    return QAGate(score=score, flags=flags, regenerations=0)


def maybe_regenerate_messages(
    *,
    client: OpenAI,
    model: str,
    wedge_name: str,
    trigger: str,
    sequence,
    messages: MessagesBundle,
    qa: QAGate,
    max_regens: int = 2,
) -> Tuple[MessagesBundle, QAGate]:
    """
    If QA score is too low or flags are serious, regenerate copy up to N times.
    """
    threshold = 0.78
    regens = 0

    while qa.score < threshold and regens < max_regens:
        regens += 1
        messages = run_copywriter(
            client=client,
            model=model,
            goal="activation",
            wedge_name=wedge_name,
            trigger=trigger,
            sequence=sequence,
        )
        qa = run_evaluator(client=client, model=model, wedge_name=wedge_name, messages=messages)
        qa.regenerations = regens

    return messages, qa


def run_explain(
    *,
    client: OpenAI,
    model: str,
    cohort: CohortInsight,
    flow: FlowSpec,
    messages: MessagesBundle,
) -> ExplainBundle:
    payload = {
        "cohort": cohort.model_dump(),
        "flow": flow.model_dump(),
        "message_intent_summary": {
            "email": "remove friction and prompt first consult setup",
            "sms": "short reminder with low barrier CTA",
            "in_app": "gentle safety net with help option",
        },
    }

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": EXPLAIN_SYSTEM},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
    )

    content = resp.choices[0].message.content or "{}"
    data = json.loads(_json_only(content))
    return ExplainBundle(**data)
