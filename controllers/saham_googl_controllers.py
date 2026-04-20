import joblib
import pandas as pd
import schemas.saham_schemas as schema

model_googl = joblib.load("datasets/model_xgb_prodcution_googl.pkl")

def make_prediction_googl(data: schema.PredictRequest):
    try:
        x_googl = pd.DataFrame([{
            "Open": data.open,
            "High": data.high,
            "Low": data.low,
            "Volume": data.volume,
        }])

        prediction = model_googl.predict(x_googl)[0]
        decision = "NAIK" if prediction > data.open else "TURUN"

        return {
            "symbol": "GOOGL",
            "predict_close": round(float(prediction), 2),
            "decision": f"Nilai Saham Diperkirakan {decision}"
        }
    except Exception as e:
        return {
                    "symbol": "GOOGL",
                    "predict_close": 0.0,
                    "decision": f"error model{str(e)}"
                }
