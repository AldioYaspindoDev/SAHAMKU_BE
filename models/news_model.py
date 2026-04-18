from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from datetime import datetime
from config.database import Base

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String, index=True)
    summary = Column(String, index=True)
    url = Column(String, index=True)
    image = Column(String, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)