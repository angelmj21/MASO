from .providers import get_fundamentals, get_technicals, get_quant, get_governance
from .mock_registry import MOCK_DATA, get_malicious_payload

class DataOrchestrator:
    def __init__(self, ticker, use_mock=False):
        self.ticker = ticker.upper()
        self.use_mock = use_mock

    def get_all_analyst_data(self):
        """Main entry point for Person 1 (Backend)."""
        if self.use_mock and self.ticker in MOCK_DATA:
            return MOCK_DATA[self.ticker]
        
        # Attempt to fetch real data
        data = {
            "fundamental": get_fundamentals(self.ticker),
            "technical": get_technicals(self.ticker),
            "quantitative": get_quant(self.ticker),
            "governance": get_governance(self.ticker)
        }
        return data

    def get_rogue_scenario(self):
        """Special helper for the Demo mode."""
        return get_malicious_payload()