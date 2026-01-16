import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update

from core.config import AppConfig
from core.metrics import compute_speedup_metrics
from core.utils import JobManager, human_dt
from agents.runner import build_autopilot_job

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


APP_TITLE = "Lifecycle Autopilot - Heidi Growth AI Enablement"

config = AppConfig.load()
jobs = JobManager()

EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    title=APP_TITLE,
    assets_folder="assets",
)
server = app.server


def heidi_logo():
    # Simple “Heidi-like” wordmark (no trademark graphics, just typography vibe)
    return html.Div(
        className="heidi-brand",
        children=[
            html.Span("Heidi", className="heidi-brand-text"),
            html.Span(" Autopilot", className="heidi-brand-sub"),
        ],
    )


def top_announcement():
    return html.Div(
        className="top-announcement",
        children=[
            html.Span("Growth AI Enablement Project  •  "),
            html.Span("Lifecycle Autopilot turns event logs → deploy-ready flows in ~60 seconds"),
            html.Span("  →", className="arrow"),
        ],
    )


def nav_bar():
    return html.Div(
        className="nav-wrap",
        children=[
            heidi_logo(),
            html.Div(
                className="nav-links",
                children=[
                    html.Div("Product", className="nav-link"),
                    html.Div("Workflows", className="nav-link"),
                    html.Div("Deploy", className="nav-link"),
                    html.Div("Explainability", className="nav-link"),
                ],
            ),
            html.Div(
                className="nav-actions",
                children=[
                    dbc.Button("Log in", outline=True, className="pill-btn pill-outline"),
                    dbc.Button("Generate", className="pill-btn pill-primary", id="nav-generate"),
                ],
            ),
        ],
    )


def hero_section():
    return html.Div(
        className="hero",
        children=[
            html.Div(
                className="hero-left",
                children=[
                    html.Div("AI trusted and loved by growth teams", className="hero-kicker"),
                    html.H1(
                        [
                            "Get time ",
                            html.Span("back", className="hero-em"),
                            ".",
                            html.Br(),
                            "Move ",
                            html.Span("growth", className="hero-em"),
                            " forward.",
                        ],
                        className="hero-title",
                    ),
                    html.P(
                        "Upload a lifecycle event log. Autopilot detects the highest-impact drop-off, "
                        "builds a 3-touch sequence (Email → SMS → In-app), generates variants, "
                        "runs a healthcare-aware QA gate, and exports deploy-ready JSON.",
                        className="hero-subtitle",
                    ),
                    html.Div(
                        className="hero-cta-row",
                        children=[
                            dbc.Button("Get Autopilot free", id="cta-generate", className="pill-btn pill-primary hero-cta"),
                            html.Div("No deck. No polish theater. Just a working system.", className="hero-note"),
                        ],
                    ),
                    html.Div(
                        className="hero-metrics-row",
                        children=[
                            html.Div(
                                className="hero-metric",
                                children=[
                                    html.Div("24.8×", className="hero-metric-val"),
                                    html.Div("faster to first draft", className="hero-metric-label"),
                                ],
                            ),
                            html.Div(
                                className="hero-metric",
                                children=[
                                    html.Div("3 → 30", className="hero-metric-val"),
                                    html.Div("flows per week", className="hero-metric-label"),
                                ],
                            ),
                            html.Div(
                                className="hero-metric",
                                children=[
                                    html.Div("4", className="hero-metric-val"),
                                    html.Div("agents + QA gate", className="hero-metric-label"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="hero-right",
                children=[
                    html.Div(
                        className="preview-card",
                        children=[
                            html.Div(
                                className="preview-top",
                                children=[
                                    html.Span("Lifecycle Flow Preview", className="preview-title"),
                                    html.Span("Shadow Mode", className="badge badge-shadow", id="mode-badge"),
                                ],
                            ),
                            html.Div(
                                className="preview-body",
                                children=[
                                    html.Div(
                                        className="preview-row",
                                        children=[
                                            html.Span("Wedge", className="preview-k"),
                                            html.Span("No first consult created within 48h", className="preview-v"),
                                        ],
                                    ),
                                    html.Div(
                                        className="preview-row",
                                        children=[
                                            html.Span("Sequence", className="preview-k"),
                                            html.Span("Email → SMS → In-app (3 variants each)", className="preview-v"),
                                        ],
                                    ),
                                    html.Div(
                                        className="preview-row",
                                        children=[
                                            html.Span("QA Gate", className="preview-k"),
                                            html.Span("Healthcare-safe copy + low spam risk", className="preview-v"),
                                        ],
                                    ),
                                    html.Hr(className="hr-soft"),
                                    html.Div(
                                        className="preview-mini",
                                        children=[
                                            html.Div("✓ Parsing events…", className="mini-line"),
                                            html.Div("✓ Cohort Detective found 11% drop-off…", className="mini-line"),
                                            html.Div("⏳ Flow Architect designing…", className="mini-line"),
                                            html.Div("⏳ Copywriter generating variants…", className="mini-line"),
                                            html.Div("⏳ Evaluator scoring + regenerating if needed…", className="mini-line"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="stack-cards",
                        children=[
                            html.Div(className="stack-card small", children=[html.Div("Export", className="stack-h"), html.Div("Braze/Iterable JSON", className="stack-p")]),
                            html.Div(className="stack-card small", children=[html.Div("Adopt", className="stack-h"), html.Div("Shadow → Assisted → Auto", className="stack-p")]),
                            html.Div(className="stack-card small", children=[html.Div("Explain", className="stack-h"), html.Div("Narrative reasoning", className="stack-p")]),
                        ],
                    ),
                ],
            ),
        ],
    )


def left_console():
    return html.Div(
        className="left-console",
        children=[
            html.Div(
                className="panel",
                children=[
                    html.Div("Input", className="panel-title"),
                    dcc.Upload(
                        id="upload-events",
                        children=html.Div(["Drag & drop event CSV, or ", html.Span("browse", className="linkish")]),
                        className="upload-box",
                        multiple=False,
                    ),
                    html.Div(id="upload-meta", className="upload-meta"),
                    html.Div(className="spacer-8"),
                    html.Div("Goal", className="field-label"),
                    dcc.Dropdown(
                        id="goal",
                        options=[
                            {"label": "Activation (recommended)", "value": "activation"},
                            {"label": "Follow-up completion", "value": "followup"},
                            {"label": "Re-engagement", "value": "reengage"},
                        ],
                        value="activation",
                        clearable=False,
                        className="heidi-dropdown",
                    ),
                    html.Div(className="spacer-8"),
                    html.Div("Wedge", className="field-label"),
                    dcc.Dropdown(
                        id="wedge",
                        options=[
                            {"label": "No first consult created within 48h", "value": "no_consult_48h"},
                            {"label": "Consult completed but note not finalized in 2h", "value": "note_not_finalized_2h"},
                            {"label": "Follow-up due but not booked within 14d", "value": "followup_not_booked_14d"},
                        ],
                        value="no_consult_48h",
                        clearable=False,
                        className="heidi-dropdown",
                    ),
                    html.Div(className="spacer-8"),
                    html.Div("Adoption Mode", className="field-label"),
                    dcc.RadioItems(
                        id="mode",
                        options=[
                            {"label": "Shadow", "value": "shadow"},
                            {"label": "Assisted", "value": "assisted"},
                            {"label": "Auto", "value": "auto"},
                        ],
                        value="shadow",
                        className="mode-toggle",
                        inputClassName="mode-radio",
                        labelClassName="mode-label",
                    ),
                    html.Div(className="spacer-8"),
                    dbc.Button(
                        "Generate Autopilot Flow",
                        id="btn-generate",
                        className="pill-btn pill-primary full-width",
                        n_clicks=0,
                    ),
                    html.Div(className="spacer-8"),
                    dbc.Button(
                        "Open Explain Drawer",
                        id="btn-explain",
                        className="pill-btn pill-outline full-width",
                        n_clicks=0,
                    ),
                ],
            ),
            html.Div(
                className="panel",
                children=[
                    html.Div("Integrations", className="panel-title"),
                    dbc.Button(
                        "Export JSON",
                        id="btn-export",
                        className="pill-btn pill-outline full-width",
                        n_clicks=0,
                        disabled=True,
                    ),
                    html.Div(className="spacer-8"),
                    dbc.Button(
                        "Send Summary to Slack",
                        id="btn-slack",
                        className="pill-btn pill-outline full-width",
                        n_clicks=0,
                        disabled=not bool(config.slack_webhook_url),
                    ),
                    html.Div(
                        "Slack button is enabled only if SLACK_WEBHOOK_URL is set.",
                        className="muted-small",
                    ),
                ],
            ),
        ],
    )


def stepper():
    return html.Div(
        className="stepper",
        children=[
            html.Div("Agents at work", className="panel-title"),
            html.Div(id="progress-lines", className="progress-lines"),
        ],
    )


def detect_tab():
    return html.Div(
        className="tab-wrap",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            className="panel big",
                            children=[
                                html.Div("Detected Bottleneck", className="panel-title"),
                                html.Div(id="detected-cohort-title", className="big-title"),
                                html.Div(id="detected-cohort-desc", className="muted"),
                                html.Div(className="spacer-12"),
                                dbc.Row(
                                    [
                                        dbc.Col(html.Div(className="metric-card", children=[
                                            html.Div("Cohort size", className="metric-k"),
                                            html.Div(id="metric-size", className="metric-v"),
                                        ])),
                                        dbc.Col(html.Div(className="metric-card", children=[
                                            html.Div("Drop-off rate", className="metric-k"),
                                            html.Div(id="metric-rate", className="metric-v"),
                                        ])),
                                        dbc.Col(html.Div(className="metric-card", children=[
                                            html.Div("Urgency", className="metric-k"),
                                            html.Div(id="metric-urgency", className="metric-v"),
                                        ])),
                                    ],
                                    className="g-3",
                                ),
                            ],
                        ),
                        width=8,
                    ),
                    dbc.Col(
                        html.Div(
                            className="panel big",
                            children=[
                                html.Div("Dataset Snapshot", className="panel-title"),
                                html.Div(id="dataset-stats", className="muted"),
                                html.Div(className="spacer-8"),
                                html.Div(id="dataset-preview", className="table-wrap"),
                            ],
                        ),
                        width=4,
                    ),
                ],
                className="g-4",
            ),
        ],
    )


def flow_tab():
    return html.Div(
        className="tab-wrap",
        children=[
            html.Div(
                className="panel big",
                children=[
                    html.Div("Flow Timeline", className="panel-title"),
                    html.Div(id="flow-trigger", className="muted"),
                    html.Div(className="spacer-12"),
                    html.Div(id="flow-timeline", className="timeline"),
                ],
            ),
            html.Div(className="spacer-16"),
            html.Div(
                className="panel big",
                children=[
                    html.Div("Deployment Payload", className="panel-title"),
                    html.Div("Braze/Iterable-compatible JSON (exportable)", className="muted-small"),
                    html.Pre(id="flow-json", className="json-box"),
                ],
            ),
        ],
    )


def messages_tab():
    return html.Div(
        className="tab-wrap",
        children=[
            html.Div(
                className="panel big",
                children=[
                    html.Div("Messages (3 variants each)", className="panel-title"),
                    html.Div(id="messages-grid", className="messages-grid"),
                ],
            ),
            html.Div(className="spacer-16"),
            html.Div(
                className="panel big",
                children=[
                    html.Div("QA Gate", className="panel-title"),
                    html.Div(id="qa-summary", className="muted"),
                    html.Div(id="qa-flags", className="flags"),
                ],
            ),
        ],
    )


def adoption_tab():
    return html.Div(
        className="tab-wrap",
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            className="panel big",
                            children=[
                                html.Div("10× Proof (Hard Numbers)", className="panel-title"),
                                html.Div(id="proof-math", className="proof-math"),
                                html.Div(className="spacer-12"),
                                html.Div(id="proof-cards", className="proof-cards"),
                            ],
                        ),
                        width=7,
                    ),
                    dbc.Col(
                        html.Div(
                            className="panel big",
                            children=[
                                html.Div("Adoption Plan", className="panel-title"),
                                html.Div(id="adoption-plan", className="adoption"),
                            ],
                        ),
                        width=5,
                    ),
                ],
                className="g-4",
            ),
        ],
    )


def explain_drawer():
    return dbc.Offcanvas(
        id="explain-drawer",
        title="Explain (Narrative Reasoning)",
        is_open=False,
        placement="end",
        className="explain-drawer",
        children=[
            html.Div(id="explain-content", className="explain-content"),
        ],
    )


def toast_area():
    return html.Div(
        id="toast-area",
        className="toast-area",
        children=[],
    )


def footer_credit():
    return html.Div(
        className="footer-credit",
        children="Built by Shyam Karthick for the Heidi Junior Engineer Program.",
    )


app.layout = html.Div(
    className="app-shell",
    children=[
        top_announcement(),
        nav_bar(),
        hero_section(),
        html.Div(
            className="console-wrap",
            children=[
                dcc.Store(id="store-job-id"),
                dcc.Store(id="store-result"),
                dcc.Store(id="store-df-meta"),
                dcc.Interval(id="poll", interval=600, n_intervals=0, disabled=True),

                html.Div(className="console-left", children=[left_console()]),
                html.Div(
                    className="console-main",
                    children=[
                        stepper(),
                        html.Div(className="spacer-12"),
                        dbc.Tabs(
                            [
                                dbc.Tab(detect_tab(), label="Detect", tab_id="tab-detect"),
                                dbc.Tab(flow_tab(), label="Build Flow", tab_id="tab-flow"),
                                dbc.Tab(messages_tab(), label="Messages + QA", tab_id="tab-messages"),
                                dbc.Tab(adoption_tab(), label="Adoption + ROI", tab_id="tab-adoption"),
                            ],
                            id="tabs",
                            active_tab="tab-detect",
                            className="heidi-tabs",
                        ),
                    ],
                ),
            ],
        ),
        explain_drawer(),
        toast_area(),
        footer_credit(),
    ],
)


def _decode_upload(contents: str) -> bytes:
    _, b64 = contents.split(",", 1)
    return base64.b64decode(b64)


def _preview_table(df: pd.DataFrame, n=7):
    view = df.head(n).copy()
    # keep it compact
    cols = list(view.columns)[:6]
    view = view[cols]
    header = html.Thead(html.Tr([html.Th(c) for c in cols]))
    body = html.Tbody([html.Tr([html.Td(str(view.iloc[i][c])) for c in cols]) for i in range(len(view))])
    return dbc.Table([header, body], bordered=False, hover=True, responsive=True, className="heidi-table")


def _mode_badge(mode: str):
    if mode == "shadow":
        return ("Shadow Mode", "badge badge-shadow")
    if mode == "assisted":
        return ("Assisted Mode", "badge badge-assisted")
    return ("Auto Mode", "badge badge-auto")


@app.callback(
    Output("upload-meta", "children"),
    Output("dataset-stats", "children"),
    Output("dataset-preview", "children"),
    Output("store-df-meta", "data"),
    Input("upload-events", "contents"),
    State("upload-events", "filename"),
)
def on_upload(contents, filename):
    if not contents:
        return ("No file uploaded yet.", "—", "—", no_update)

    try:
        raw = _decode_upload(contents)
        df = pd.read_csv(pd.io.common.BytesIO(raw))
        meta = {
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "columns": list(df.columns),
            "filename": filename or "events.csv",
        }
        upload_meta = f"Uploaded: {meta['filename']} • {meta['rows']} rows • {meta['cols']} columns"
        stats = f"Columns: {', '.join(meta['columns'][:8])}" + ("…" if len(meta["columns"]) > 8 else "")
        preview = _preview_table(df)
        return upload_meta, stats, preview, meta
    except Exception as e:
        return f"Upload failed: {e}", "—", "—", no_update


@app.callback(
    Output("store-job-id", "data"),
    Output("poll", "disabled"),
    Output("tabs", "active_tab"),
    Input("btn-generate", "n_clicks"),
    Input("cta-generate", "n_clicks"),
    Input("nav-generate", "n_clicks"),
    State("upload-events", "contents"),
    State("goal", "value"),
    State("wedge", "value"),
    State("mode", "value"),
    prevent_initial_call=True,
)
def start_job(n1, n2, n3, contents, goal, wedge, mode):
    trigger = (n1 or 0) + (n2 or 0) + (n3 or 0)
    if trigger <= 0:
        return no_update, no_update, no_update
    if not contents:
        return no_update, no_update, no_update

    raw = _decode_upload(contents)

    job_id = jobs.create_job()
    job_fn = build_autopilot_job(
        job_id=job_id,
        raw_csv=raw,
        goal=goal,
        wedge=wedge,
        mode=mode,
        config=config,
        exports_dir=str(EXPORTS_DIR),
        jobs=jobs,
    )
    jobs.run(job_id, job_fn)

    # enable polling + jump to Detect tab
    return job_id, False, "tab-detect"


@app.callback(
    Output("progress-lines", "children"),
    Output("store-result", "data"),
    Output("btn-export", "disabled"),
    Output("btn-slack", "disabled"),
    Output("mode-badge", "children"),
    Output("mode-badge", "className"),
    Input("poll", "n_intervals"),
    State("store-job-id", "data"),
    State("mode", "value"),
)
def poll_job(_, job_id, mode):
    label, klass = _mode_badge(mode)
    if not job_id:
        return [html.Div("Awaiting input…", className="progress-line")], no_update, True, (not bool(config.slack_webhook_url)), label, klass

    status = jobs.get(job_id)
    if not status:
        return [html.Div("Job not found.", className="progress-line error")], no_update, True, (not bool(config.slack_webhook_url)), label, klass

    lines = []
    for item in status.progress:
        css = "progress-line done" if item.get("done") else "progress-line"
        if item.get("kind") == "error":
            css = "progress-line error"
        lines.append(html.Div(item.get("text", ""), className=css))

    export_enabled = False
    slack_enabled = bool(config.slack_webhook_url)

    result_data = no_update
    if status.done and status.result:
        export_enabled = True
        # slack enabled only if webhook exists AND we have a result
        slack_enabled = bool(config.slack_webhook_url)
        result_data = status.result

    return lines, result_data, (not export_enabled), (not slack_enabled), label, klass


def _safe_get(d: Dict[str, Any], path: str, default="—"):
    cur: Any = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _render_timeline(sequence):
    # sequence: list of steps
    items = []
    for step in sequence:
        items.append(
            html.Div(
                className="timeline-item",
                children=[
                    html.Div(step.get("t_plus"), className="timeline-time"),
                    html.Div(
                        className="timeline-card",
                        children=[
                            html.Div(step.get("channel", "").upper(), className="timeline-channel"),
                            html.Div(step.get("goal", ""), className="timeline-goal"),
                            html.Div(step.get("cta", ""), className="timeline-cta"),
                        ],
                    ),
                ],
            )
        )
    return items


def _render_messages(messages: Dict[str, Any]):
    # messages: {"email": {...}, "sms": {...}, "in_app": {...}}
    cards = []
    for ch_key in ["email", "sms", "in_app"]:
        ch = messages.get(ch_key, {})
        variants = ch.get("variants", [])
        title = ch.get("title", ch_key.replace("_", " ").title())
        cards.append(
            html.Div(
                className="msg-card",
                children=[
                    html.Div(title, className="msg-title"),
                    html.Div(ch.get("notes", ""), className="muted-small"),
                    html.Div(
                        className="msg-variants",
                        children=[
                            html.Div(
                                className="variant",
                                children=[
                                    html.Div(f"Variant {i+1}", className="variant-h"),
                                    html.Pre(v.get("text", ""), className="variant-body"),
                                    html.Div(
                                        className="variant-meta",
                                        children=[
                                            html.Span(f"Tone: {v.get('tone','—')}", className="chip"),
                                            html.Span(f"CTA: {v.get('cta','—')}", className="chip"),
                                        ],
                                    ),
                                ],
                            )
                            for i, v in enumerate(variants)
                        ],
                    ),
                ],
            )
        )
    return cards


@app.callback(
    Output("detected-cohort-title", "children"),
    Output("detected-cohort-desc", "children"),
    Output("metric-size", "children"),
    Output("metric-rate", "children"),
    Output("metric-urgency", "children"),
    Output("flow-trigger", "children"),
    Output("flow-timeline", "children"),
    Output("flow-json", "children"),
    Output("messages-grid", "children"),
    Output("qa-summary", "children"),
    Output("qa-flags", "children"),
    Output("proof-math", "children"),
    Output("proof-cards", "children"),
    Output("adoption-plan", "children"),
    Output("explain-content", "children"),
    Input("store-result", "data"),
    State("mode", "value"),
)
def render_result(result, mode):
    if not result:
        # Empty state
        empty = "—"
        return (
            "Upload events and click Generate.",
            "Autopilot will detect the highest-impact lifecycle bottleneck.",
            empty, empty, empty,
            empty, [], "—",
            [],
            "—", [],
            "", [],
            "",
            html.Div("Generate a flow to see narrative reasoning here.", className="muted"),
        )

    cohort_title = _safe_get(result, "cohort.name")
    cohort_desc = _safe_get(result, "cohort.story")
    size = _safe_get(result, "cohort.size")
    rate = _safe_get(result, "cohort.dropoff_rate")
    urgency = _safe_get(result, "cohort.urgency")

    trigger = _safe_get(result, "flow.trigger")
    sequence = _safe_get(result, "flow.sequence", default=[])
    timeline = _render_timeline(sequence if isinstance(sequence, list) else [])

    export_json = json.dumps(result.get("deploy_payload", result), indent=2)

    msgs = result.get("messages", {})
    messages_grid = _render_messages(msgs if isinstance(msgs, dict) else {})

    qa = result.get("qa", {})
    qa_summary = f"Score: {qa.get('score','—')} • Regenerations: {qa.get('regenerations','—')} • Mode: {mode}"
    flags = qa.get("flags", []) or []
    flag_elems = [html.Span(f, className="flag") for f in flags] if flags else [html.Span("No flags.", className="flag ok")]

    # hard numbers proof
    metrics = compute_speedup_metrics()
    proof_math = html.Div(
        className="proof-math-inner",
        children=[
            html.Div(f"{metrics['speedup']:.1f}× faster", className="proof-big"),
            html.Div(
                f"{metrics['manual_total_min']} min → {metrics['ai_total_min']} min per flow",
                className="muted",
            ),
        ],
    )
    proof_cards = html.Div(
        className="proof-cards-inner",
        children=[
            html.Div(className="proof-card", children=[html.Div("Manual / flow", className="metric-k"), html.Div(f"{metrics['manual_total_hr']} hrs", className="metric-v")]),
            html.Div(className="proof-card", children=[html.Div("AI / flow", className="metric-k"), html.Div(f"{metrics['ai_total_min']} min", className="metric-v")]),
            html.Div(className="proof-card", children=[html.Div("Throughput", className="metric-k"), html.Div("3 → 30 flows/week", className="metric-v")]),
            html.Div(className="proof-card", children=[html.Div("Result", className="metric-k"), html.Div(f"{metrics['speedup']:.2f}×", className="metric-v")]),
        ],
    )

    adoption = result.get("adoption", {})
    adoption_plan = html.Ul(
        className="adoption-list",
        children=[
            html.Li([html.B("Shadow: "), adoption.get("shadow", "AI proposes; humans approve.")]),
            html.Li([html.B("Assisted: "), adoption.get("assisted", "AI pre-fills; approval for deploy.")]),
            html.Li([html.B("Auto: "), adoption.get("auto", "AI deploys low-risk flows; human spot-check weekly.")]),
        ],
    )

    explain = result.get("explain", {})
    explain_content = html.Div(
        className="explain-sections",
        children=[
            html.Div(className="explain-section", children=[html.Div("Why this cohort?", className="explain-h"), html.Div(explain.get("why_cohort", "—"), className="explain-p")]),
            html.Div(className="explain-section", children=[html.Div("Why these timings?", className="explain-h"), html.Div(explain.get("why_timing", "—"), className="explain-p")]),
            html.Div(className="explain-section", children=[html.Div("Why this message?", className="explain-h"), html.Div(explain.get("why_message", "—"), className="explain-p")]),
        ],
    )

    return (
        cohort_title,
        cohort_desc,
        str(size),
        str(rate),
        str(urgency),
        f"Trigger: {trigger}",
        timeline,
        export_json,
        messages_grid,
        qa_summary,
        flag_elems,
        proof_math,
        proof_cards,
        adoption_plan,
        explain_content,
    )


@app.callback(
    Output("explain-drawer", "is_open"),
    Input("btn-explain", "n_clicks"),
    Input("tabs", "active_tab"),
    State("explain-drawer", "is_open"),
    prevent_initial_call=True,
)
def toggle_explain(btn, tab, is_open):
    # open on button click; keep stable on tab switch
    if btn:
        return not is_open
    return is_open


@app.callback(
    Output("toast-area", "children"),
    Input("btn-export", "n_clicks"),
    Input("btn-slack", "n_clicks"),
    State("store-result", "data"),
    State("store-job-id", "data"),
    prevent_initial_call=True,
)
def actions(export_clicks, slack_clicks, result, job_id):
    ctx = dash.callback_context
    if not ctx.triggered or not result:
        return no_update
    trig = ctx.triggered[0]["prop_id"].split(".")[0]

    toasts = []
    now = human_dt(datetime.utcnow())
    if trig == "btn-export":
        out_path = EXPORTS_DIR / f"{job_id or 'latest'}_flow.json"
        latest_path = EXPORTS_DIR / "latest_flow.json"
        out_path.write_text(json.dumps(result.get("deploy_payload", result), indent=2))
        latest_path.write_text(json.dumps(result.get("deploy_payload", result), indent=2))
        toasts.append(
            dbc.Toast(
                [html.Div("Exported deploy-ready JSON."), html.Div(str(out_path), className="muted-small")],
                header=f"Export complete • {now}",
                is_open=True,
                dismissable=True,
                icon="success",
                duration=4500,
                className="heidi-toast",
            )
        )
    elif trig == "btn-slack":
        # Slack send is performed in backend job; here we just confirm UX.
        toasts.append(
            dbc.Toast(
                ["Slack summary dispatched (if webhook configured)."],
                header=f"Slack • {now}",
                is_open=True,
                dismissable=True,
                icon="primary",
                duration=4500,
                className="heidi-toast",
            )
        )

    return toasts


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", "8050")))
