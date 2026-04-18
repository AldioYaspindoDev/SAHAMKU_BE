from sqlalchemy.engine import result
import yfinance as yf
from datetime import datetime, timedelta


def get_market_overview():
    tickers = {
        "NVDA": "NVDA",
        "AAPL": "AAPL",
        "GOOGL": "GOOGL",
        "TSLA": "TSLA",
        "MSFT": "MSFT",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW JONES": "^DJI",
        "FTSE 100": "^FTSE",
        "NIKKEI 225": "^N225",
        "BTCUSD": "BTC-USD",
    }

    result = []

    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")

        if not data.empty:
            current_price = data['Close'].iloc[-1]
            open_price = data['Open'].iloc[0]
            change = current_price - open_price
            percentage_change = (change / open_price) * 100

            result.append({
                "name": name,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "percentage_change": round(percentage_change, 2)
            })
    return result

def get_market_status():
    now = datetime.now()
    if now.weekday() < 5:
        return "OPEN"
    return "CLOSED"

def get_historical_data(symbol: str, period: str = "1mo"):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)

    chart_data = [
        {
            "date": index.strftime("%Y-%m-%d"),
            "price": round(price, 2),
        }
        for index, price in data["Close"].items()
    ]
    return chart_data
    
    