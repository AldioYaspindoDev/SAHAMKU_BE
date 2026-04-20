from fastapi import APIRouter
import schemas.saham_schemas as schema
import controllers.saham_googl_controllers as googl

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post("/googl", response_model=schema.PredictResponse)
def predict_googl(request: schema.PredictRequest):
    return googl.make_prediction_googl(request)