from fastapi import APIRouter
import schemas.saham_schemas as schemas
import controllers.saham_appl_controllers as controllers

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post("/aapl", response_model=schemas.PredictResponse)
def predict_appl(request: schemas.PredictRequest):
    return controllers.make_prediction_appl(request)