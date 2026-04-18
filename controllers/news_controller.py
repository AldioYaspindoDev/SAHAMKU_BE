import requests
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models.news_model as news 
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_economic_news(db: Session):

    latest_news = db.query(news.News).order_by(news.News.fetched_at.desc()).first()

    if latest_news and (datetime.utcnow() - latest_news.fetched_at) < timedelta(hours=1):
        logger.info("MENGAMBIL DARI DATABASE (hemat token)")
        return db.query(news.News).limit(6).all()

    print("get api")
    api_key = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        news_data = response.json()[:6]
        db.query(news.News).delete()

        for item in news_data:
            new_entry = news.News(
                headline=item.get('headline'),
                summary=item.get('summary'),
                url=item.get('url'),
                image=item.get('image'),
                fetched_at=datetime.utcnow()
            )
            db.add(new_entry)
        
        db.commit()
        return db.query(news.News).all()
    return []


