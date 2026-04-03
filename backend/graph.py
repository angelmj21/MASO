"""
LangGraph StateGraph pipeline — 4 nodes:

  Node 1  fetch_market_data     — pulls live yfinance data
  Node 2  agent_swarm           — fan-out to 4 analysts, fan-in results
  Node 3  strategy_orchestrator — weighted scoring → TradePlan
  Node 4  armoriq_validation    — ArmorIQ IAP intent capture + execution check
"""
from typing import TypedDict, Annotated, Optional
import operator

from langgraph.graph import StateGraph, START, END

from data_layer  import DataOrchestrator
from agents     import fundamental_agent, quant_agent, technical_agent, governance_agent
from orchestrator import generate_trade_plan
from security   import run_security_check
from models     import AgentResult, TradePlan, ArmorIQStatus
from utils      import syslog, seclog


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class GraphState(TypedDict):
    ticker:  str
    prompt:  str
    logs:    Annotated[list[str], operator.add]  # all nodes append; LangGraph merges
    stock:   dict
    agents:  Annotated[list, operator.add]        # parallel fan-in
    trade:   Optional[TradePlan]
    armoriq: Optional[ArmorIQStatus]


# ---------------------------------------------------------------------------
# Node 1 — Fetch market data
# ---------------------------------------------------------------------------

def fetch_market_data(state: GraphState) -> dict:
    stock = DataOrchestrator(state["ticker"]).get_all_analyst_data()
    return {
        "stock": stock,
        "logs":  [syslog("Fetching market data")],
    }


# ---------------------------------------------------------------------------
# Node 2 — Agent swarm (parallel fan-out / fan-in)
# ---------------------------------------------------------------------------

def node_fundamental(state: GraphState) -> dict:
    return {"agents": [fundamental_agent(state["ticker"], state["stock"])]}


def node_quant(state: GraphState) -> dict:
    return {"agents": [quant_agent(state["ticker"], state["stock"])]}


def node_technical(state: GraphState) -> dict:
    return {"agents": [technical_agent(state["ticker"], state["stock"])]}


def node_governance(state: GraphState) -> dict:
    return {"agents": [governance_agent(state["ticker"], state["stock"])]}


# ---------------------------------------------------------------------------
# Node 3 — Strategy orchestrator
# ---------------------------------------------------------------------------

def strategy_orchestrator(state: GraphState) -> dict:
    # Preserve canonical agent order regardless of parallel completion order
    order = ["Fundamental Agent", "Quant Agent", "Technical Agent", "Governance Agent"]
    sorted_agents = sorted(
        state["agents"],
        key=lambda a: order.index(a.name) if a.name in order else 99,
    )
    trade = generate_trade_plan(state["ticker"], sorted_agents)
    return {
        "trade": trade,
        "logs":  [syslog(f"Strategy orchestrator generated plan: {trade.action} {trade.ticker} x{trade.quantity}")],
    }


# ---------------------------------------------------------------------------
# Node 4 — ArmorIQ security validation
# ---------------------------------------------------------------------------

def armoriq_validation(state: GraphState) -> dict:
    result, sec_logs = run_security_check(state["trade"], state["prompt"])
    
    update_payload = {
        "armoriq": result,
        "logs": sec_logs,
    }
    
    # CRUCIAL FIX: Mutate the TradePlan if the execution was blocked by an attack
    # This ensures the React UI clearly shows the attempted rogue action
    if result.status == "BLOCKED":
        update_payload["trade"] = TradePlan(
            action="SELL_ALL", 
            ticker=state["ticker"], 
            quantity=100000, 
            confidence_score=99.99
        )
        
    return update_payload


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    g = StateGraph(GraphState)

    g.add_node("fetch_market_data",     fetch_market_data)
    g.add_node("fundamental",           node_fundamental)
    g.add_node("quant",                 node_quant)
    g.add_node("technical",             node_technical)
    g.add_node("governance",            node_governance)
    g.add_node("strategy_orchestrator", strategy_orchestrator)
    g.add_node("armoriq_validation",    armoriq_validation)

    # START → fetch data (sequential)
    g.add_edge(START, "fetch_market_data")

    # fetch → all four agents (parallel fan-out)
    g.add_edge("fetch_market_data", "fundamental")
    g.add_edge("fetch_market_data", "quant")
    g.add_edge("fetch_market_data", "technical")
    g.add_edge("fetch_market_data", "governance")

    # all agents → orchestrator (fan-in)
    g.add_edge("fundamental",  "strategy_orchestrator")
    g.add_edge("quant",        "strategy_orchestrator")
    g.add_edge("technical",    "strategy_orchestrator")
    g.add_edge("governance",   "strategy_orchestrator")

    # orchestrator → ArmorIQ → END
    g.add_edge("strategy_orchestrator", "armoriq_validation")
    g.add_edge("armoriq_validation",    END)

    return g


def run_graph(ticker: str, prompt: str) -> GraphState:
    """Compile and invoke the full pipeline. Returns the final state."""
    compiled = build_graph().compile()
    return compiled.invoke({
        "ticker":  ticker,
        "prompt":  prompt,
        "logs":    [syslog("Initializing MASO agents"), syslog("Running LangGraph pipeline")],
        "stock":   {},
        "agents":  [],
        "trade":   None,
        "armoriq": None,
    })