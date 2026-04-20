import joblib
import pandas as pd
import schemas.saham_schemas as saham

model_appl = joblib.load("datasets/model_xgb_prodcution_appl.pkl")

def make_prediction_appl(data: saham.PredictRequest):
    try:
        X_appl = pd.DataFrame([{
            "Open": data.open,
            "High": data.high,
            "Low": data.low,
            "Volume": data.volume
        }])

        prediction = model_appl.predict(X_appl)[0]
        decision = "NAIK" if prediction > data.open else "TURUN"

        return {
            "symbol": "APPL",
            "predict_close": round(float(prediction), 2),
            "decision": f"Nilai Saham Diperkirakan {decision}"
        }
    except Exception as e:
        return {"symbol": "APPL", "predict_close": 0.0, "decision": f"error model {str(e)}"}