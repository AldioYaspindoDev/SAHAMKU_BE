from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.database import get_db
import controllers.news_controller as news_logic

router = APIRouter(prefix="/news", tags=["Economic News"])

@router.get("/")
def get_latest_news(db: Session = Depends(get_db)):
    news = news_logic.get_economic_news(db)
    return news