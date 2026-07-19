from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from config.database import Base

class admin_model(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(Integer, unique=True, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), ondelete=func.now())