import yfinance as yf


_EMPTY_RESPONSE = {
    "ticker":        "N/A",
    "current_price": 0,
    "market_cap":    0,
    "52_week_high":  0,
    "52_week_low":   0,
    "status":        "error",
    "message":       "Ticker symbol cannot be empty.",
}


def get_stock_data(ticker: str) -> dict:
    """Fetch live market data from yfinance."""
    if not ticker or not ticker.strip():
        return _EMPTY_RESPONSE.copy()
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker.upper(),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
        "market_cap":    info.get("marketCap", 0),
        "52_week_high":  info.get("fiftyTwoWeekHigh", 0),
        "52_week_low":   info.get("fiftyTwoWeekLow", 0),
    }
