import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file before any other local imports so GEMINI_API_KEY
# and ARMORIQ_API_KEY are in os.environ when agents.py is imported.
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import run_graph

app = FastAPI(title="MASO – Multi-Agent Strategy Orchestrator")

# NOTE: set allow_credentials=True and restrict allow_origins if auth cookies/headers are needed in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    ticker: str = "AAPL"
    prompt: str = "Analyze AAPL for a long position"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    print(f"\n\n🚨🚨🚨 INITIATING MASO BACKEND FOR: {request.ticker} 🚨🚨🚨\n\n")
    state = run_graph(request.ticker, request.prompt)

    # Preserve canonical agent order in the response
    order = ["Fundamental Agent", "Quant Agent", "Technical Agent", "Governance Agent"]
    sorted_agents = sorted(
        state["agents"],
        key=lambda a: order.index(a.name) if a.name in order else 99,
    )

    return {
        "logs":    state["logs"],
        "stock":   state["stock"],
        "agents":  [a.model_dump() for a in sorted_agents],
        "trade":   state["trade"].model_dump(),
        "armoriq": state["armoriq"].model_dump(),
    }