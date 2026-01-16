from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd


REQUIRED_COLS = {"user_id", "event_name", "timestamp"}


@dataclass(frozen=True)
class ParsedEvents:
    df: pd.DataFrame
    total_users: int
    total_events: int


def parse_csv_bytes(raw_csv: bytes) -> ParsedEvents:
    df = pd.read_csv(io.BytesIO(raw_csv))
    # Normalize likely naming variants
    df = df.rename(
        columns={
            "event": "event_name",
            "timestamp_utc": "timestamp",
            "time": "timestamp",
        }
    )

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    # ensure types
    df["user_id"] = df["user_id"].astype(str)
    df["event_name"] = df["event_name"].astype(str)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    # drop bad timestamps
    df = df.dropna(subset=["timestamp"]).sort_values(["user_id", "timestamp"]).reset_index(drop=True)

    total_users = df["user_id"].nunique()
    total_events = len(df)
    return ParsedEvents(df=df, total_users=total_users, total_events=total_events)


def wedge_stats(df: pd.DataFrame, wedge: str) -> Dict:
    """
    Compute cohort size / rate for a selected wedge.
    Wedges are intentionally Heidi-ish: consult/note/follow-up.
    """
    users = df["user_id"].unique().tolist()
    total_users = len(users)

    # helpful helpers
    def has_event(u: str, event: str) -> bool:
        return (df[(df["user_id"] == u) & (df["event_name"] == event)].shape[0]) > 0

    def first_time(u: str, event: str):
        sub = df[(df["user_id"] == u) & (df["event_name"] == event)]
        if sub.empty:
            return None
        return sub["timestamp"].min().to_pydatetime()

    cohort = []

    if wedge == "no_consult_48h":
        for u in users:
            t_signup = first_time(u, "signup_completed") or first_time(u, "email_verified")
            if not t_signup:
                continue
            t_consult = first_time(u, "consult_created")
            if not t_consult and (t_signup + timedelta(hours=48)) < df["timestamp"].max().to_pydatetime():
                cohort.append(u)

        cohort_name = "No first consult created within 48h"
        urgency = "High"

    elif wedge == "note_not_finalized_2h":
        for u in users:
            t_consult_done = first_time(u, "consult_completed")
            if not t_consult_done:
                continue
            t_note_final = first_time(u, "note_finalized")
            if not t_note_final and (t_consult_done + timedelta(hours=2)) < df["timestamp"].max().to_pydatetime():
                cohort.append(u)
        cohort_name = "Consult completed but note not finalized within 2h"
        urgency = "Medium"

    elif wedge == "followup_not_booked_14d":
        for u in users:
            t_due = first_time(u, "followup_due")
            if not t_due:
                continue
            t_booked = first_time(u, "followup_booked")
            if not t_booked and (t_due + timedelta(days=14)) < df["timestamp"].max().to_pydatetime():
                cohort.append(u)
        cohort_name = "Follow-up due but not booked within 14 days"
        urgency = "Medium"

    else:
        raise ValueError(f"Unknown wedge: {wedge}")

    size = len(set(cohort))
    rate = (size / total_users) if total_users else 0.0
    return {
        "wedge": wedge,
        "cohort_name": cohort_name,
        "cohort_size": size,
        "total_users": total_users,
        "dropoff_rate": f"{round(rate * 100)}%",
        "urgency_hint": urgency,
        "cohort_user_ids": cohort[:500],  # keep bounded
    }
