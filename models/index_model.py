"""
Models untuk fitur Index Analytics (LQ45, IDX30, dst).

Struktur relasional:
    Index (1) ---- (banyak) Period ---- (banyak) Constituent
    Index (1) ---- (banyak) Analytics   <- hasil hitungan, bukan data mentah

Kenapa dipisah dari models/saham_*.py yang sudah ada: fitur ini
domainnya beda (index BEI, bukan prediksi harga per-ticker), jadi
dikasih namespace tabel sendiri (prefix "index_") biar tidak
tabrakan dengan tabel lain di project ini.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    BigInteger, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class IndexModel(Base):
    __tablename__ = "indices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # "LQ45", "IDX30", dst

    periods = relationship("PeriodModel", back_populates="index", cascade="all, delete-orphan")
    analytics = relationship("AnalyticsModel", back_populates="index", cascade="all, delete-orphan")


class PeriodModel(Base):
    __tablename__ = "index_periods"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(Integer, ForeignKey("indices.id"), nullable=False)

    evaluation_type = Column(String, nullable=True)     # Mayor / Minor
    effective_start = Column(Date, nullable=False)
    effective_end = Column(Date, nullable=True)
    announcement_no = Column(String, nullable=True)
    source_filename = Column(String, nullable=True)
    has_weight_data = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    index = relationship("IndexModel", back_populates="periods")
    constituents = relationship("ConstituentModel", back_populates="period", cascade="all, delete-orphan")

    __table_args__ = (
        # Kunci idempotency: 1 index cuma boleh punya 1 periode dengan
        # tanggal efektif yang sama. Upload file yang sama 2x -> UPDATE,
        # bukan duplikat.
        UniqueConstraint("index_id", "effective_start", name="uq_period_index_start"),
    )


class ConstituentModel(Base):
    __tablename__ = "index_constituents"

    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("index_periods.id"), nullable=False)

    stock_code = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    free_float_ratio = Column(Float, nullable=True)
    shares_pra = Column(BigInteger, nullable=True)
    shares_pasca = Column(BigInteger, nullable=True)
    shares_status = Column(String, nullable=True)
    weight_pra = Column(Float, nullable=True)
    weight_pasca = Column(Float, nullable=True)
    weight_status = Column(String, nullable=True)

    period = relationship("PeriodModel", back_populates="constituents")

    __table_args__ = (
        UniqueConstraint("period_id", "stock_code", name="uq_constituent_period_stock"),
    )


class AnalyticsModel(Base):
    """
    Tabel hasil hitungan (bukan data mentah). Selalu di-OVERWRITE
    setiap kali recompute dijalankan setelah ada upload baru — jadi
    endpoint GET analytics tinggal query tabel ini, tidak perlu
    hitung ulang on-the-fly setiap request.
    """
    __tablename__ = "index_analytics"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(Integer, ForeignKey("indices.id"), nullable=False)
    stock_code = Column(String, index=True, nullable=False)

    frequency = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    is_perfect_member = Column(Boolean, default=False)
    simple_consistency_score = Column(Float, default=0.0)

    # Metrik berbasis bobot — nullable karena tidak semua periode
    # historis (misal sebelum 2025) punya data bobot.
    average_weight = Column(Float, nullable=True)
    weight_std = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)

    last_computed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    index = relationship("IndexModel", back_populates="analytics")

    __table_args__ = (
        UniqueConstraint("index_id", "stock_code", name="uq_analytics_index_stock"),
    )
