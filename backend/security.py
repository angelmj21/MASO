"""
ArmorIQ Intent Assurance Plane (IAP) — SDK simulation.

Mirrors ArmorIQ's documented IAP architecture:
  1. capture_plan     — HMAC-SHA256 signs the canonical trade plan (the "plan root")
  2. get_intent_token — issues a short-lived UUID token binding this context to the plan
  3. validate_execution — any deviation from the signed plan → BLOCKED

ARMORIQ_API_KEY is read from the environment; falls back to a demo placeholder
so the server starts without a real key during development.

Prompt-injection detection:
  Prompts containing any ATTACK_KEYWORDS are flagged as rogue.
  The trader then attempts SELL_ALL, which mismatches the signed plan → BLOCKED.
"""
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone

from models import TradePlan, ArmorIQStatus
from utils  import seclog

# Attack phrases — checked against a space-stripped, uppercased prompt
# to defeat homoglyph and extra-space bypass attempts (e.g. "S E L L  A L L")
_ATTACK_KEYWORDS_NORMALIZED = ["IGNOREINSTRUCTIONS", "LIQUIDATE", "SELLALL", "SELL_ALL"]
ROGUE_ACTION = "SELL_ALL:PORTFOLIO:10000"


def is_rogue_prompt(prompt: str) -> bool:
    normalized = prompt.upper().replace(" ", "")
    return any(kw in normalized for kw in _ATTACK_KEYWORDS_NORMALIZED)


class ArmorIQClient:
    """Simulated ArmorIQ SDK client (mirrors armoriq-sdk interface)."""

    def __init__(self):
        _key = os.getenv("ARMORIQ_API_KEY", "demo-key-placeholder")
        if _key == "demo-key-placeholder" or not _key:
            raise RuntimeError(
                "ARMORIQ_API_KEY is not set or is still the demo placeholder. "
                "Set a real secret before running: export ARMORIQ_API_KEY=your_secret"
            )
        self._api_key  = _key
        self._canonical: str = ""
        self._plan_hash: str = ""

    def capture_plan(self, trade: TradePlan) -> str:
        """Serialise and HMAC-SHA256-sign the trade plan. Returns the plan hash."""
        self._canonical = f"{trade.action.upper()}:{trade.ticker.upper()}:{trade.quantity}"
        self._plan_hash = hmac.new(
            key=self._api_key.encode(),
            msg=self._canonical.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        return self._plan_hash

    def get_intent_token(self) -> str:
        """Issue a short-lived intent token tied to this execution context."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"iq-{uuid.uuid4().hex[:16]}-{ts}"

    def validate_execution(self, token: str, attempted_action: str) -> ArmorIQStatus:
        """Compare attempted action against the signed plan. Block on any mismatch."""
        if attempted_action == self._canonical:
            return ArmorIQStatus(
                status="APPROVED",
                token_id=token,
                plan_hash=self._plan_hash,
                blocked_reason=None,
            )
        return ArmorIQStatus(
            status="BLOCKED",
            token_id=token,
            plan_hash=self._plan_hash,
            blocked_reason="Intent mismatch – outside authorized scope",
        )


def run_security_check(
    trade: TradePlan, prompt: str
) -> tuple[ArmorIQStatus, list[str]]:
    """
    Full ArmorIQ IAP flow.
    Returns (ArmorIQStatus, timestamped_security_logs).
    """
    logs: list[str] = []
    client = ArmorIQClient()

    logs.append(seclog("Capturing intent via ArmorIQ"))
    client.capture_plan(trade)

    token = client.get_intent_token()
    logs.append(seclog("Policy check: execution must match signed intent"))

    rogue = is_rogue_prompt(prompt)
    if rogue:
        logs.append(seclog("Rogue prompt injection detected"))
        attempted = ROGUE_ACTION
    else:
        attempted = f"{trade.action.upper()}:{trade.ticker.upper()}:{trade.quantity}"

    logs.append(seclog("Validating execution"))
    result = client.validate_execution(token, attempted)

    # Stamp the proof-of-authorization token onto the plan itself
    trade.token_id = token

    if result.status == "BLOCKED":
        logs.append(seclog("ACTION BLOCKED"))
    else:
        logs.append(seclog("Execution APPROVED by ArmorIQ"))

    return result, logs
