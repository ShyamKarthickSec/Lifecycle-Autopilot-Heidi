from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, conlist


# ---- Cohort ----
class CohortInsight(BaseModel):
    name: str = Field(..., description="Short cohort name")
    story: str = Field(..., description="Narrative explanation of why this cohort matters")
    size: int = Field(..., ge=0)
    dropoff_rate: str = Field(..., description="e.g., '11%'")
    urgency: Literal["Low", "Medium", "High"]


# ---- Flow ----
class FlowStep(BaseModel):
    t_plus: str = Field(..., description="e.g., 'T+48h'")
    channel: Literal["email", "sms", "in_app"]
    goal: str
    cta: str


class FlowSpec(BaseModel):
    trigger: str
    sequence: conlist(FlowStep, min_length=1, max_length=6)


# ---- Copy ----
class MessageVariant(BaseModel):
    tone: str
    cta: str
    text: str


class ChannelMessagePack(BaseModel):
    title: str
    notes: str
    variants: conlist(MessageVariant, min_length=1, max_length=5)


class MessagesBundle(BaseModel):
    email: ChannelMessagePack
    sms: ChannelMessagePack
    in_app: ChannelMessagePack


# ---- QA ----
class QAGate(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)
    regenerations: int = 0


# ---- Explain narrative ----
class ExplainBundle(BaseModel):
    why_cohort: str
    why_timing: str
    why_message: str


# ---- Full result ----
class AutopilotResult(BaseModel):
    cohort: CohortInsight
    flow: FlowSpec
    messages: MessagesBundle
    qa: QAGate
    explain: ExplainBundle
    adoption: Dict[str, str]
    deploy_payload: Dict[str, Any]
