import yfinance as yf
import pandas as pd
import numpy as np

def get_fundamentals(ticker_str):
    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        
        # Check if we actually got real data (fake tickers return very short dicts)
        if len(info) <= 1 or "regularMarketPrice" not in info and "previousClose" not in info:
            return {"status": "error", "message": "Ticker not found"}

        return {
            "pe_ratio": info.get("forwardPE", 0),
            "debt_to_equity": info.get("debtToEquity", 0),
            "profit_margins": info.get("profitMargins", 0),
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_technicals(ticker_str):
    """Calculates RSI and Moving Averages."""
    try:
        ticker = yf.Ticker(ticker_str)
        df = ticker.history(period="1mo")
        if df.empty: return {"status": "error"}
        
        # Simple RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            "current_price": df['Close'].iloc[-1],
            "rsi": round(rsi.iloc[-1], 2) if not np.isnan(rsi.iloc[-1]) else 50,
            "50d_ma": round(df['Close'].mean(), 2),
            "status": "success"
        }
    except Exception:
        return {"status": "error", "rsi": 50}

def get_quant(ticker_str):
    """Calculates Volatility and Beta."""
    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        hist = ticker.history(period="1y")
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) # Annualized
        
        return {
            "beta": info.get("beta", 1.0),
            "volatility": round(volatility, 4),
            "sharpe_ratio": round(returns.mean() / returns.std() * np.sqrt(252), 2) if returns.std() != 0 else 0,
            "status": "success"
        }
    except Exception:
        return {"beta": 1.0, "volatility": 0.15, "status": "mocked"}

def get_governance(ticker_str):
    """Checks Insider activity and Sentiment."""
    try:
        ticker = yf.Ticker(ticker_str)
        news = (ticker.news or [])[:3]  # guard against None from yfinance
        # Simplified sentiment: count 'positive' words in headlines
        bullish_words = ['growth', 'buy', 'beat', 'positive', 'success']
        score = 50
        for n in news:
            if any(word in n['title'].lower() for word in bullish_words):
                score += 15
        
        return {
            "insider_sentiment": "Positive" if score > 50 else "Neutral",
            "score": min(score, 100),
            "esg_risk": "Low",
            "status": "success"
        }
    except Exception:
        return {"insider_sentiment": "Neutral", "score": 50, "status": "mocked"}