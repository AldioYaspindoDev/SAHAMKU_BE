from fastapi import APIRouter
import schemas.saham_schemas as schema
import controllers.saham_controller as controller

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post("/nvda", response_model=schema.PredictResponse)
def predict_nvda_simple(request: schema.PredictRequest):
    return controller.make_prediction_simple(request)