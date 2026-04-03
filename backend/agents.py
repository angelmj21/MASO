"""
Four AI analyst agents powered by Google Gemini (gemini-1.5-flash).

Each agent receives a domain-relevant slice of the stock data, sends a
structured prompt to Gemini requesting a JSON response, parses the result,
and returns an AgentResult Pydantic model.

Fallback: if the Gemini API fails for any reason (rate-limit, timeout,
bad JSON, network error) the agent returns a safe deterministic HOLD at
score 50 so the LangGraph pipeline never crashes during a live demo.
"""
import os
import json
import hashlib
import time

from google import genai
from google.genai import types

from models import AgentResult

# ── Gemini client ─────────────────────────────────────────────────────────────
_gemini_api_key = os.getenv("GEMINI_API_KEY")
if not _gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable is missing! "
        "Add it to backend/.env: GEMINI_API_KEY=your_key_here"
    )

_client = genai.Client(api_key=_gemini_api_key)
_MODEL = "gemini-2.5-flash"
_GEN_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json"
)

# ── Deterministic fallback (MD5-seeded) ───────────────────────────────────────
def _fallback_score(ticker: str, salt: str, base: int, spread: int) -> int:
    digest = hashlib.md5(f"{ticker.upper()}{salt}".encode()).hexdigest()
    return min(100, base + int(digest[:4], 16) % spread)


def _fallback(name: str, ticker: str, salt: str, base: int, spread: int) -> AgentResult:
    score  = _fallback_score(ticker, salt, base, spread)
    signal = "BUY" if score >= 65 else ("HOLD" if score >= 45 else "SELL")
    return AgentResult(
        name=name,
        score=score,
        signal=signal,
        reasoning="API timeout — defaulting to safety parameters.",
    )


# ── Shared Gemini caller ───────────────────────────────────────────────────────
def _call_gemini(
    name: str,
    ticker: str,
    domain: str,
    domain_data: dict,
    fallback_salt: str,
    fallback_base: int,
    fallback_spread: int,
) -> AgentResult:
    """
    Build a structured prompt, call Gemini, parse the JSON response.
    Falls back to a deterministic mock on any exception.
    """
    prompt = (
        f"You are a {domain} AI Agent analyzing ticker {ticker}. "
        f"Here is the live market data: {json.dumps(domain_data)}. "
        f"Based on this data, evaluate the asset. "
        f"You MUST return a JSON object with exactly three keys: "
        f"'score' (integer 0-100), "
        f"'signal' (string, one of 'BUY', 'SELL', or 'HOLD'), and "
        f"'reasoning' (string, max 2 sentences explaining your conclusion "
        f"based on the data)."
    )

    try:
        response = _client.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=_GEN_CONFIG,
        )
        parsed    = json.loads(response.text)
        score     = int(parsed["score"])
        signal    = str(parsed["signal"]).upper().strip()
        reasoning = str(parsed["reasoning"]).strip()

        if signal not in ("BUY", "SELL", "HOLD"):
            signal = "HOLD"

        return AgentResult(name=name, score=score, signal=signal, reasoning=reasoning)

    except Exception as exc:  # noqa: BLE001
        print(f"[{name}] Gemini call failed ({type(exc).__name__}: {exc}) — using fallback")
        return _fallback(name, ticker, fallback_salt, fallback_base, fallback_spread)


# ── Domain data slices ────────────────────────────────────────────────────────
# data.py returns a flat dict. Each agent receives the keys relevant to its
# domain. If the stock dict ever gains sub-keys (e.g. stock['fundamental']),
# those are preferred; otherwise the flat keys are used as the slice.

def _fundamental_slice(stock: dict) -> dict:
    return stock.get("fundamental") or {
        "current_price": stock.get("current_price"),
        "market_cap":    stock.get("market_cap"),
        "52_week_high":  stock.get("52_week_high"),
        "52_week_low":   stock.get("52_week_low"),
    }


def _technical_slice(stock: dict) -> dict:
    return stock.get("technical") or {
        "current_price": stock.get("current_price"),
        "52_week_high":  stock.get("52_week_high"),
        "52_week_low":   stock.get("52_week_low"),
    }


def _quant_slice(stock: dict) -> dict:
    return stock.get("quantitative") or {
        "current_price": stock.get("current_price"),
        "market_cap":    stock.get("market_cap"),
        "52_week_high":  stock.get("52_week_high"),
        "52_week_low":   stock.get("52_week_low"),
    }


def _governance_slice(stock: dict) -> dict:
    return stock.get("governance") or {
        "ticker":     stock.get("ticker"),
        "market_cap": stock.get("market_cap"),
    }


# ── Public agent functions ────────────────────────────────────────────────────

def fundamental_agent(ticker: str, stock: dict) -> AgentResult:
    return _call_gemini(
        name="Fundamental Agent",
        ticker=ticker,
        domain="Fundamental Analysis",
        domain_data=_fundamental_slice(stock),
        fallback_salt="fundamental",
        fallback_base=58,
        fallback_spread=28,
    )


def quant_agent(ticker: str, stock: dict) -> AgentResult:
    time.sleep(2)
    return _call_gemini(
        name="Quant Agent",
        ticker=ticker,
        domain="Quantitative Analysis",
        domain_data=_quant_slice(stock),
        fallback_salt="quant",
        fallback_base=62,
        fallback_spread=24,
    )


def technical_agent(ticker: str, stock: dict) -> AgentResult:
    time.sleep(4)
    return _call_gemini(
        name="Technical Agent",
        ticker=ticker,
        domain="Technical Analysis",
        domain_data=_technical_slice(stock),
        fallback_salt="technical",
        fallback_base=52,
        fallback_spread=32,
    )


def governance_agent(ticker: str, stock: dict) -> AgentResult:
    time.sleep(6)
    return _call_gemini(
        name="Governance Agent",
        ticker=ticker,
        domain="ESG and Governance Analysis",
        domain_data=_governance_slice(stock),
        fallback_salt="governance",
        fallback_base=66,
        fallback_spread=18,
    )


def run_all_agents(ticker: str, stock: dict) -> list[AgentResult]:
    """Run all four agents in canonical order: Fundamental → Quant → Technical → Governance."""
    return [
        fundamental_agent(ticker, stock),
        quant_agent(ticker, stock),
        technical_agent(ticker, stock),
        governance_agent(ticker, stock),
    ]
