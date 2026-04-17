from typing import Optional
from pydantic import BaseModel

class PredictRequest(BaseModel):
    open: float
    high: float
    low: float
    volume: float

class PredictResponse(BaseModel):
    symbol: str
    predict_close: float
    decision: str