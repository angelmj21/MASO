from data_layer import DataOrchestrator

def test_edge_case(name, ticker, use_mock=False):
    print(f"\n>>> 🔍 TESTING: {name} (Ticker: '{ticker}')")
    try:
        orch = DataOrchestrator(ticker, use_mock=use_mock)
        data = orch.get_all_analyst_data()
        
        # Check if the structure is maintained even on failure
        required_keys = ["fundamental", "technical", "quantitative", "governance"]
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"❌ FAIL: Missing categories {missing}")
        else:
            print(f"✅ PASS: Structure is intact.")
            # Check if it gracefully handled the bad data
            status = data['fundamental'].get('status')
            print(f"   Response Status: {status}")

    except Exception as e:
        print(f"💥 CRASH: The system didn't handle this! Error: {e}")

if __name__ == "__main__":
    print("=== MASO EDGE CASE STRESS TEST ===")

    # Case 1: The "Fake" Ticker (Typo check)
    test_edge_case("Non-Existent Ticker", "XYZ_NOT_REAL_123")

    # Case 2: The "Empty" Ticker (User hits enter with no text)
    test_edge_case("Empty String", "")

    # Case 3: Cryptocurrency (Testing if yfinance handles different formats)
    test_edge_case("Crypto Ticker", "BTC-USD")

    # Case 4: International Stocks (Testing suffix support)
    test_edge_case("International Ticker", "RELIANCE.NS")

    # Case 5: The "Mock Fallback" check
    # Testing a ticker NOT in your mock_registry while mock=True
    test_edge_case("Unregistered Mock Ticker", "MSFT", use_mock=True)

    print("\n=== Stress Test Complete ===")