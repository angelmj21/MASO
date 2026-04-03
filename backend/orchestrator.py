from models import AgentResult, TradePlan

WEIGHTS: dict[str, float] = {
    "Fundamental Agent": 0.35,
    "Quant Agent":       0.25,
    "Technical Agent":   0.20,
    "Governance Agent":  0.20,
}


def generate_trade_plan(ticker: str, agents: list[AgentResult]) -> TradePlan:
    """Weighted scoring across all agents → TradePlan."""
    confidence = round(
        sum(a.score * WEIGHTS.get(a.name, 0) for a in agents), 2
    )
    buy_w  = sum(WEIGHTS.get(a.name, 0) for a in agents if a.signal == "BUY")
    sell_w = sum(WEIGHTS.get(a.name, 0) for a in agents if a.signal == "SELL")
    action = "BUY" if buy_w >= sell_w else "SELL"

    return TradePlan(
        action=action,
        ticker=ticker.upper(),
        quantity=150,
        confidence_score=confidence,
    )
