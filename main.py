from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import engine, Base
from models import user_model
from api.endpoint import all_routers

# Buat semua tabel di database secara otomatis saat server start
Base.metadata.create_all(bind=engine)

# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title="Sahamku API",
    description="REST API backend untuk aplikasi Sahamku",
    version="1.0.0",
)

# Tambahkan Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Izinkan semua origin (untuk development)
    allow_credentials=True,
    allow_methods=["*"], # Izinkan semua method (GET, POST, OPTIONS, dll)
    allow_headers=["*"], # Izinkan semua header
)


# ───────────────────────────────────────
# Root endpoint — cek apakah server hidup
# ───────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {"message": "Server running with PostgreSQL"}


# ───────────────────────────────────────
# Daftarkan semua router dari api/endpoint.py
# ───────────────────────────────────────
for router in all_routers:
    app.include_router(router)