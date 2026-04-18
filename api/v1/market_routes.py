from fastapi import APIRouter
import controllers.market_controllers as market

router = APIRouter(prefix="/market", tags=["Market"])

@router.get("/overview")
def get_market_overview():
    return market.get_market_overview()

@router.get("/market/status")
def get_market_status():
    return market.get_market_status()

@router.get("/history/{symbol}")
def get_stock_history(symbol: str):
    return market.get_historical_data(symbol)