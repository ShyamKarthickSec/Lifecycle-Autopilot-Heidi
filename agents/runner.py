from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from openai import OpenAI

from core.config import AppConfig
from core.event_parser import parse_csv_bytes, wedge_stats
from core.schemas import AutopilotResult
from core.utils import send_slack, JobManager
from agents.cohort_detective import run_cohort_detective
from agents.flow_architect import run_flow_architect
from agents.copywriter import run_copywriter
from agents.evaluator import run_evaluator, maybe_regenerate_messages, run_explain


def build_deploy_payload(mode: str, cohort: Dict[str, Any], flow: Dict[str, Any], messages: Dict[str, Any], qa: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mode affects gating + payload shape.
    """
    payload = {
        "cohort": cohort,
        "flow": flow,
        "messages": messages,
        "qa": qa,
        "mode": mode,
    }

    if mode == "shadow":
        payload["deployment"] = {
            "status": "draft",
            "review_required": True,
            "notes": "Shadow mode: suggestions only. Human approval required before any deploy.",
        }

    elif mode == "assisted":
        payload["deployment"] = {
            "status": "ready_for_approval",
            "review_required": True,
            "template_fields": {
                "campaign_name": f"Autopilot — {cohort['name']}",
                "audience_rule": flow["trigger"],
                "channels": [s["channel"] for s in flow["sequence"]],
                "holdout_pct": 10,
            },
            "notes": "Assisted mode: prefilled deploy fields. Human approval required to push to lifecycle tool.",
        }

    else:  # auto
        # choose best variant per channel by simple heuristic: shortest + evaluator score
        # (real system could run variant scoring; for demo we keep deterministic)
        best = {}
        for ch in ["email", "sms", "in_app"]:
            variants = messages[ch]["variants"]
            best[ch] = min(variants, key=lambda v: len(v.get("text", "")))

        payload["deployment"] = {
            "status": "api_ready",
            "review_required": False,
            "sunset_rules": {
                "min_sends": 500,
                "sunset_if_ctr_below": 0.10,
            },
            "selected_variants": best,
            "notes": "Auto mode: API-ready payload + sunset rules. Human spot-check weekly.",
        }

    return payload


def build_autopilot_job(
    *,
    job_id: str,
    raw_csv: bytes,
    goal: str,
    wedge: str,
    mode: str,
    config: AppConfig,
    exports_dir: str,
    jobs: JobManager,
):
    """
    Returns a no-arg callable suitable for JobManager.run().
    """
    exports = Path(exports_dir)
    client = OpenAI(api_key=config.openai_api_key)

    def p(text: str, done: bool = False, kind: str = "info"):
        jobs.update(job_id, text, done=done, kind=kind)

    def job_fn() -> Dict[str, Any]:
        p("✓ Parsing events…")
        parsed = parse_csv_bytes(raw_csv)
        p(f"✓ Analyzing {parsed.total_users:,} user journeys / {parsed.total_events:,} events…")

        stats = wedge_stats(parsed.df, wedge=wedge)
        p(f"✓ Cohort prepared: {stats['cohort_size']:,} users ({stats['dropoff_rate']})…")

        p("⏳ Cohort Detective reasoning…")
        cohort = run_cohort_detective(
            client=client,
            model=config.model_fast,
            goal=goal,
            wedge_name=stats["cohort_name"],
            wedge=stats["wedge"],
            cohort_size=stats["cohort_size"],
            dropoff_rate=stats["dropoff_rate"],
            total_users=stats["total_users"],
            urgency_hint=stats["urgency_hint"],
        )
        p("✓ Cohort Detective completed.", done=True)

        p("⏳ Flow Architect designing sequence…")
        flow = run_flow_architect(
            client=client,
            model=config.model_fast,
            goal=goal,
            wedge_name=stats["cohort_name"],
            urgency=cohort.urgency,
        )
        p("✓ Flow Architect completed.", done=True)

        p("⏳ Copywriter generating variants…")
        messages = run_copywriter(
            client=client,
            model=config.model_quality,
            goal=goal,
            wedge_name=stats["cohort_name"],
            trigger=flow.trigger,
            sequence=flow.sequence,
        )
        p("✓ Copywriter completed.", done=True)

        p("⏳ Evaluator scoring + regenerating if needed…")
        qa = run_evaluator(
            client=client,
            model=config.model_fast,
            wedge_name=stats["cohort_name"],
            messages=messages,
        )

        messages, qa = maybe_regenerate_messages(
            client=client,
            model=config.model_quality,
            wedge_name=stats["cohort_name"],
            trigger=flow.trigger,
            sequence=flow.sequence,
            messages=messages,
            qa=qa,
            max_regens=2,
        )
        p("✓ QA Gate completed.", done=True)

        p("⏳ Explainability layer writing narrative…")
        explain = run_explain(
            client=client,
            model=config.model_fast,
            cohort=cohort,
            flow=flow,
            messages=messages,
        )
        p("✓ Explain completed.", done=True)

        adoption = {
            "shadow": "AI proposes flows with confidence + review checkpoints. Nothing auto-deploys.",
            "assisted": "AI pre-fills deploy templates and suggests holdout. Human approval required to export.",
            "auto": "AI outputs API-ready payloads, chooses best variants, and suggests sunset rules. Human spot-check weekly.",
        }

        deploy_payload = build_deploy_payload(
            mode=mode,
            cohort=cohort.model_dump(),
            flow=flow.model_dump(),
            messages=messages.model_dump(),
            qa=qa.model_dump(),
        )

        result = AutopilotResult(
            cohort=cohort,
            flow=flow,
            messages=messages,
            qa=qa,
            explain=explain,
            adoption=adoption,
            deploy_payload=deploy_payload,
        ).model_dump()

        # Write exports
        exports.mkdir(exist_ok=True)
        out_path = exports / f"{job_id}_flow.json"
        latest_path = exports / "latest_flow.json"
        out_path.write_text(json.dumps(deploy_payload, indent=2))
        latest_path.write_text(json.dumps(deploy_payload, indent=2))

        # Optional Slack summary
        if config.slack_webhook_url:
            text = (
                f"*Lifecycle Autopilot generated a flow*\n"
                f"• Cohort: {cohort.name} ({cohort.dropoff_rate})\n"
                f"• Trigger: {flow.trigger}\n"
                f"• QA score: {qa.score}\n"
                f"• Mode: {mode}\n"
            )
            send_slack(config.slack_webhook_url, text)

        p("✓ Export ready.", done=True)
        return result

    return job_fn
