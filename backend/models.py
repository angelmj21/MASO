from pydantic import BaseModel
from typing import Optional


class AgentResult(BaseModel):
    name: str
    score: int
    signal: str          # BUY | SELL | HOLD
    reasoning: str


class TradePlan(BaseModel):
    action: str
    ticker: str
    quantity: int
    confidence_score: float
    token_id: Optional[str] = None  # ArmorIQ proof-of-authorization badge


class ArmorIQStatus(BaseModel):
    status: str          # APPROVED | BLOCKED
    token_id: str
    plan_hash: str
    blocked_reason: Optional[str] = None
