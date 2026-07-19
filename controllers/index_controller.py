"""
Controller utama untuk fitur Index Analytics.

Alur:
    upload file -> ingest_excel_file() -> simpan Period+Constituent ke DB
                                        -> trigger recompute_analytics()
    GET analytics -> get_simple_consistency() -> query tabel Analytics
"""

from datetime import datetime
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models.index_model import IndexModel, PeriodModel, ConstituentModel, AnalyticsModel
from controllers.index_parser_controller import parse_bei_index_excel


# =============================================================
# INGESTION
# =============================================================

def get_or_create_index(db: Session, index_name: str) -> IndexModel:
    index_name = index_name.strip().upper()
    idx = db.query(IndexModel).filter(IndexModel.name == index_name).first()
    if idx is None:
        idx = IndexModel(name=index_name)
        db.add(idx)
        db.commit()
        db.refresh(idx)
    return idx


def ingest_excel_file(db: Session, index_name: str, filename: str, file_bytes: bytes, trigger_recompute: bool = True) -> dict:
    """
    Parse file Excel lalu upsert ke database secara idempotent:
      - Kalau periode (index, effective_start) BELUM ada -> insert baru
      - Kalau SUDAH ada (misal file di-upload ulang / revisi BEI)
        -> constituent lama dihapus, diganti dengan yang baru

    trigger_recompute=False dipakai saat upload BANYAK file sekaligus
    (batch), supaya recompute_analytics() cuma jalan SEKALI di akhir
    setelah semua file selesai di-ingest — bukan berulang kali per file.

    Return dict ringkasan untuk response API.
    """
    parsed = parse_bei_index_excel(file_bytes, source_filename=filename)

    idx = get_or_create_index(db, index_name)

    period = (
        db.query(PeriodModel)
        .filter(
            PeriodModel.index_id == idx.id,
            PeriodModel.effective_start == parsed["effective_start"],
        )
        .first()
    )
    is_update = period is not None

    if period is None:
        period = PeriodModel(index_id=idx.id)
        db.add(period)
    else:
        db.query(ConstituentModel).filter(ConstituentModel.period_id == period.id).delete()

    period.evaluation_type = parsed.get("evaluation_type")
    period.effective_start = parsed["effective_start"]
    period.effective_end = parsed.get("effective_end")
    period.source_filename = filename
    period.has_weight_data = parsed["has_weight_data"]
    period.uploaded_at = datetime.utcnow()
    db.commit()
    db.refresh(period)

    df = parsed["constituents"]
    for _, row in df.iterrows():
        def _clean(v):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return None
            return v

        db.add(ConstituentModel(
            period_id=period.id,
            stock_code=row["stock_code"],
            company_name=_clean(row.get("company_name")),
            free_float_ratio=_clean(row.get("free_float_ratio")),
            shares_pra=_clean(row.get("shares_pra")),
            shares_pasca=_clean(row.get("shares_pasca")),
            shares_status=_clean(row.get("shares_status")),
            weight_pra=_clean(row.get("weight_pra")),
            weight_pasca=_clean(row.get("weight_pasca")),
            weight_status=_clean(row.get("weight_status")),
        ))
    db.commit()

    if trigger_recompute:
        recompute_analytics(db, idx.id)

    return {
        "index_name": idx.name,
        "evaluation_type": period.evaluation_type,
        "effective_start": period.effective_start,
        "effective_end": period.effective_end,
        "n_constituents": len(df),
        "has_weight_data": period.has_weight_data,
        "is_update": is_update,
        "message": (
            f"Periode {period.effective_start} berhasil "
            f"{'diperbarui' if is_update else 'ditambahkan'} ({len(df)} saham)."
        ),
    }

# =============================================================
# Ingest Multipel Excel File
# =============================================================
def ingest_multiple_files(db: Session, index_name: str, files: list) -> dict:
    """
    Ingest BANYAK file Excel sekaligus (upload batch).

    `files` = list of (filename: str, file_bytes: bytes)

    Desain penting:
      - Setiap file diproses secara TERPISAH dengan try/except
        sendiri-sendiri. Kalau 1 dari 16 file gagal, file lainnya
        TETAP lanjut diproses — bukan seluruh batch gagal.
      - recompute_analytics() cuma dipanggil SEKALI di akhir.
    """
    idx = get_or_create_index(db, index_name)

    succeeded, failed = [], []
    for filename, file_bytes in files:
        try:
            result = ingest_excel_file(db, index_name, filename, file_bytes, trigger_recompute=False)
            succeeded.append({"filename": filename, **result})
        except ValueError as e:
            failed.append({"filename": filename, "error": str(e)})
        except Exception as e:
            failed.append({"filename": filename, "error": f"Error tak terduga: {e}"})

    n_stocks_recomputed = recompute_analytics(db, idx.id) if succeeded else 0

    return {
        "index_name": idx.name,
        "total_files": len(files),
        "n_succeeded": len(succeeded),
        "n_failed": len(failed),
        "succeeded": succeeded,
        "failed": failed,
        "n_stocks_recomputed": n_stocks_recomputed,
    }


# =============================================================
# BUILD MASTER DATAFRAME (dari DB, bukan dari file lagi)
# =============================================================

def _build_master_dataframe(db: Session, index_id: int) -> pd.DataFrame:
    """
    Ambil semua Period + Constituent milik satu index dari DB, gabung
    jadi satu DataFrame long-format, dengan period_id berurutan
    berdasarkan tanggal efektif (bukan id insert ke DB).
    """
    periods = (
        db.query(PeriodModel)
        .filter(PeriodModel.index_id == index_id)
        .order_by(PeriodModel.effective_start.asc())
        .all()
    )

    rows = []
    for seq, period in enumerate(periods, start=1):
        for c in period.constituents:
            rows.append({
                "period_id": seq,
                "effective_start": period.effective_start,
                "stock_code": c.stock_code,
                "weight_pasca": c.weight_pasca,
                "has_weight_data": period.has_weight_data,
            })

    return pd.DataFrame(rows)


# =============================================================
# ANALYTICS (logika sama seperti yang sudah divalidasi di Colab)
# =============================================================

def _min_max_normalize(series: pd.Series) -> pd.Series:
    if series.max() == series.min():
        return pd.Series(100.0, index=series.index)
    return ((series - series.min()) / (series.max() - series.min())) * 100


def _compute_frequency(master: pd.DataFrame) -> pd.DataFrame:
    return (
        master.groupby("stock_code")["period_id"]
        .nunique()
        .reset_index(name="frequency")
    )


def _compute_longest_streak(master: pd.DataFrame) -> pd.DataFrame:
    results = []
    for stock, group in master.groupby("stock_code"):
        periods_present = sorted(group["period_id"].unique())
        longest = current = 1
        for i in range(1, len(periods_present)):
            if periods_present[i] == periods_present[i - 1] + 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        results.append({"stock_code": stock, "longest_streak": longest})
    return pd.DataFrame(results)


def _compute_weight_stats(master: pd.DataFrame) -> pd.DataFrame:
    stats = (
        master.groupby("stock_code")["weight_pasca"]
        .agg(average_weight="mean", weight_std="std")
        .reset_index()
    )
    return stats


def _compute_simple_consistency(freq_df, streak_df, total_periods) -> pd.DataFrame:
    merged = freq_df.merge(streak_df, on="stock_code")
    merged["freq_norm"] = _min_max_normalize(merged["frequency"])
    merged["streak_norm"] = _min_max_normalize(merged["longest_streak"])
    merged["simple_consistency_score"] = (
        0.5 * merged["freq_norm"] + 0.5 * merged["streak_norm"]
    ).round(2)
    merged["is_perfect_member"] = merged["frequency"] == total_periods
    return merged


def recompute_analytics(db: Session, index_id: int) -> int:
    """
    Hitung ulang SEMUA metrik untuk satu index, dari SELURUH histori
    periode yang ada di DB, lalu upsert ke tabel AnalyticsModel.

    Full recompute (bukan incremental) dipilih dengan sengaja: karena
    frequency/streak sifatnya kumulatif dari seluruh histori, begitu
    ada 1 periode baru masuk, semua stock_code perlu dihitung ulang.
    Untuk skala data LQ45 (puluhan periode x ~45-80 saham) ini murah,
    tidak perlu optimasi incremental.

    Return: jumlah stock_code yang berhasil di-recompute.
    """
    master = _build_master_dataframe(db, index_id)
    if master.empty:
        return 0

    total_periods = master["period_id"].nunique()

    freq_df = _compute_frequency(master)
    streak_df = _compute_longest_streak(master)
    weight_df = _compute_weight_stats(master)
    consistency_df = _compute_simple_consistency(freq_df, streak_df, total_periods)
    consistency_df = consistency_df.merge(weight_df, on="stock_code", how="left")

    # Hapus analytics lama untuk index ini, ganti dengan hasil baru
    db.query(AnalyticsModel).filter(AnalyticsModel.index_id == index_id).delete()

    for _, row in consistency_df.iterrows():
        avg_w = row["average_weight"]
        w_std = row["weight_std"]
        db.add(AnalyticsModel(
            index_id=index_id,
            stock_code=row["stock_code"],
            frequency=int(row["frequency"]),
            longest_streak=int(row["longest_streak"]),
            is_perfect_member=bool(row["is_perfect_member"]),
            simple_consistency_score=float(row["simple_consistency_score"]),
            average_weight=None if pd.isna(avg_w) else float(avg_w),
            weight_std=None if pd.isna(w_std) else float(w_std),
            last_computed_at=datetime.utcnow(),
        ))
    db.commit()

    return len(consistency_df)


# =============================================================
# READ / QUERY
# =============================================================

def get_simple_consistency(db: Session, index_name: str) -> list:
    idx = db.query(IndexModel).filter(IndexModel.name == index_name.strip().upper()).first()
    if idx is None:
        return []
    return (
        db.query(AnalyticsModel)
        .filter(AnalyticsModel.index_id == idx.id)
        .order_by(AnalyticsModel.simple_consistency_score.desc(), AnalyticsModel.frequency.desc())
        .all()
    )


def get_periods(db: Session, index_name: str) -> list:
    idx = db.query(IndexModel).filter(IndexModel.name == index_name.strip().upper()).first()
    if idx is None:
        return []
    return (
        db.query(PeriodModel)
        .filter(PeriodModel.index_id == idx.id)
        .order_by(PeriodModel.effective_start.asc())
        .all()
    )
