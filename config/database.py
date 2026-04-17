import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Ambil URL database dari file .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Buat koneksi ke database
engine = create_engine(DATABASE_URL)

# SessionLocal digunakan untuk membuat sesi database di setiap request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base adalah kelas induk untuk semua model SQLAlchemy
Base = declarative_base()


# Dependency injection: dipakai di endpoint dengan Depends(get_db)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()