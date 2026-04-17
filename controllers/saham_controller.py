import joblib
import pandas as pd
import schemas.saham_schemas as saham 
import yfinance as yf
import numpy as np

model_simple = joblib.load("datasets/model_xgb_prodcution.pkl")

def make_prediction_simple(data: saham.PredictRequest):
    try:
        X_simple = pd.DataFrame([{
            "Open": data.open,
            "High": data.high,
            "Low": data.low,
            "Volume": data.volume
        }])
        
        prediction = model_simple.predict(X_simple)[0]
        decision = "NAIK" if prediction > data.open else "TURUN"

        return {
            "symbol": "NVDA",
            "predict_close": round(float(prediction), 2),
            "decision": f"[Simple] Nilai Saham Diperkirakan {decision}"
        }
    except Exception as e:
        return {"symbol": "NVDA", "predict_close": 0.0, "decision": f"Error Simple Model: {str(e)}"}
