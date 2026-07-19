"""
Parser untuk file Excel pengumuman resmi BEI (LQ45, dan index lain
dengan format serupa).

PENTING: logika di file ini SUDAH DIVALIDASI sebelumnya lewat 16 file
riil (2022-2026) di Google Colab — termasuk penanganan:
  - Skema kolom yang beda antar tahun (ada/tidaknya kolom Bobot)
  - Merged cell di header (pakai forward-fill)
  - 6 variasi format tanggal periode efektif BEI

Jangan ubah logika intinya tanpa re-test terhadap file-file historis
itu, karena berisiko regresi silent (salah geser kolom tanpa error).
"""

import re
from io import BytesIO
from typing import Union

import openpyxl
import pandas as pd


BULAN_MAP = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5,
    "juni": 6, "juli": 7, "agustus": 8, "september": 9,
    "oktober": 10, "november": 11, "desember": 12,
}


def _parse_tanggal_indo(text: str):
    text = text.lower().strip()
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", text)
    if m:
        day, month_name, year = m.groups()
        month = BULAN_MAP.get(month_name)
        if month:
            return pd.Timestamp(int(year), month, int(day)).date()
    m2 = re.search(r"(\w+)\s+(\d{4})", text)
    if m2:
        month_name, year = m2.groups()
        month = BULAN_MAP.get(month_name)
        if month:
            return pd.Timestamp(int(year), month, 1).date()
    return None


def _parse_effective_period(raw_text: str):
    """Parse rentang tanggal periode efektif, menangani 6 variasi
    format yang sudah ditemukan di file-file historis BEI (lihat
    docstring modul)."""
    text = raw_text.strip()
    parts = re.split(r"s\.?d\.?", text, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None, None

    start_txt, end_txt = parts[0].strip(), parts[1].strip()
    end_date = _parse_tanggal_indo(end_txt)
    if end_date is None:
        return None, None

    start_date = _parse_tanggal_indo(start_txt)
    if start_date is None:
        m = re.search(r"(\d{1,2})\s+(\w+)", start_txt.lower())
        if m:
            day, month_name = m.groups()
        else:
            m = re.search(r"(\w+)", start_txt.lower())
            day, month_name = "1", (m.group(1) if m else None)

        month = BULAN_MAP.get(month_name) if month_name else None
        if month:
            year = end_date.year
            if month > end_date.month:
                year -= 1  # rentang melewati pergantian tahun
            start_date = pd.Timestamp(year, month, int(day)).date()

    return start_date, end_date


def _detect_header_column_map(rows: list, data_start_idx: int) -> dict:
    """Deteksi otomatis posisi kolom dari blok header (schema-aware),
    dengan forward-fill untuk menangani merged cell."""
    header_rows = []
    i = data_start_idx - 1
    while i >= 0:
        row = rows[i]
        if all(c is None for c in row):
            break
        header_rows.append(row)
        i -= 1
    header_rows.reverse()

    def _ffill_row(row):
        filled, last = [], None
        for v in row:
            if v is not None:
                last = v
            filled.append(last)
        return filled

    col_text = {}
    for row in header_rows:
        for c_idx, val in enumerate(_ffill_row(row)):
            if val is None:
                continue
            txt = str(val).strip().lower()
            col_text[c_idx] = (col_text.get(c_idx, "") + " " + txt).strip()

    col_map = {}
    keterangan_cols = []
    for c_idx, txt in col_text.items():
        if txt in ("no.", "no"):
            col_map["no"] = c_idx
        elif "kode" in txt:
            col_map["stock_code"] = c_idx
        elif "nama saham" in txt:
            col_map["company_name"] = c_idx
        elif "free float" in txt:
            col_map["free_float_ratio"] = c_idx
        elif "bobot" in txt and "pra" in txt:
            col_map["weight_pra"] = c_idx
        elif "bobot" in txt and ("pasca" in txt or "hasil" in txt or "cap" in txt):
            col_map["weight_pasca"] = c_idx
        elif "jumlah saham" in txt and ("pra evaluasi" in txt or "saat ini" in txt):
            col_map["shares_pra"] = c_idx
        elif "jumlah saham" in txt and ("pasca evaluasi" in txt or "hasil evaluasi" in txt or "cap" in txt):
            col_map["shares_pasca"] = c_idx
        elif "keterangan" in txt:
            keterangan_cols.append(c_idx)

    keterangan_cols.sort()
    if len(keterangan_cols) >= 1:
        col_map["shares_status"] = keterangan_cols[0]
    if len(keterangan_cols) >= 2:
        col_map["weight_status"] = keterangan_cols[1]

    col_map["_has_weight_data"] = "weight_pasca" in col_map
    col_map["_has_company_name"] = "company_name" in col_map
    return col_map


def parse_bei_index_excel(file_source: Union[str, bytes, BytesIO], source_filename: str = None) -> dict:
    """
    Parse satu file Excel resmi pengumuman BEI (LQ45 atau index sejenis).

    file_source: path string, bytes, atau file-like object (misal
    dari `UploadFile.file` di FastAPI).

    Return dict:
        {
            "index_name": str,
            "evaluation_type": str,
            "effective_start": date,
            "effective_end": date,
            "has_weight_data": bool,
            "has_company_name": bool,
            "constituents": pd.DataFrame,
            "removed": pd.DataFrame,
        }
    """
    if isinstance(file_source, (bytes, bytearray)):
        file_source = BytesIO(file_source)

    wb = openpyxl.load_workbook(file_source, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    metadata = {}
    for row in rows[:10]:
        cells = [c for c in row if c is not None]
        if not cells:
            continue
        label = str(cells[0])
        if "Nama Indeks" in label:
            metadata["index_name"] = str(cells[-1]).replace(":", "").strip()
        elif label.strip().startswith("Evaluasi"):
            metadata["evaluation_type"] = str(cells[-1]).replace(":", "").strip()
        elif "Periode Efektif Kons" in label:
            metadata["effective_period_raw"] = str(cells[-1]).replace(":", "").strip()

    if "effective_period_raw" in metadata:
        metadata["effective_start"], metadata["effective_end"] = _parse_effective_period(
            metadata["effective_period_raw"]
        )

    if metadata.get("effective_start") is None:
        raise ValueError(
            f"Gagal membaca tanggal periode efektif dari '{source_filename}'. "
            f"Teks mentah: {metadata.get('effective_period_raw')!r}. "
            "Cek/tambahkan pola baru di _parse_effective_period()."
        )

    data_start_idx = None
    for i, row in enumerate(rows):
        if row[1] == 1 and isinstance(row[2], str):
            data_start_idx = i
            break
    if data_start_idx is None:
        raise ValueError(f"Tidak menemukan baris data konstituen di '{source_filename}'")

    col_map = _detect_header_column_map(rows, data_start_idx)
    has_weight = col_map["_has_weight_data"]
    has_company_name = col_map["_has_company_name"]

    def _get(r, key):
        idx = col_map.get(key)
        if idx is None or idx >= len(r):
            return None
        val = r[idx]
        return None if val == "-" else val

    constituent_rows = []
    i = data_start_idx
    while i < len(rows) and isinstance(rows[i][1], int):
        r = rows[i]
        constituent_rows.append({
            "stock_code": _get(r, "stock_code"),
            "company_name": _get(r, "company_name"),
            "free_float_ratio": _get(r, "free_float_ratio"),
            "shares_pra": _get(r, "shares_pra"),
            "shares_pasca": _get(r, "shares_pasca"),
            "shares_status": _get(r, "shares_status"),
            "weight_pra": _get(r, "weight_pra"),
            "weight_pasca": _get(r, "weight_pasca"),
            "weight_status": _get(r, "weight_status"),
        })
        i += 1

    df_constituents = pd.DataFrame(constituent_rows)

    removed_rows = []
    exit_header_idx = None
    for j, row in enumerate(rows):
        cells = [c for c in row if c is not None]
        if cells and "keluar dari penghitungan indeks" in str(cells[0]):
            exit_header_idx = j
            break
    if exit_header_idx is not None:
        k = exit_header_idx
        while k < len(rows):
            row = rows[k]
            if row[1] == "No." and row[2] == "Kode":
                k += 2
                break
            k += 1
        while k < len(rows) and isinstance(rows[k][1], int):
            r = rows[k]
            removed_rows.append({"stock_code": r[2], "company_name": r[3]})
            k += 1

    df_removed = pd.DataFrame(removed_rows)

    return {
        **metadata,
        "has_weight_data": has_weight,
        "has_company_name": has_company_name,
        "constituents": df_constituents,
        "removed": df_removed,
    }
