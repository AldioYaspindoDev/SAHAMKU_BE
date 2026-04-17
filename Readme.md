# 📊 US Stock Analytics Platform – Multi-Ticker XGBoost

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![XGBoost](https://img.shields.io/badge/XGBoost-2.1+-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)

Platform analitik saham **US Market** yang melayani **lebih dari 100 emiten** (AAPL, NVDA, MSFT, TSLA, dll). Sistem ini menggabungkan **XGBoost** untuk pemodelan statistik, **FastAPI** sebagai backend inferensi, **Next.js** untuk dashboard interaktif, dan **PostgreSQL** untuk manajemen data historis serta metadata model.

> **Fokus utama:** analisis pergerakan harga berdasarkan **data historis murni** (lag features) – tidak ada *look-ahead bias*, semua prediksi hanya menggunakan informasi yang tersedia hingga hari sebelumnya.

---

## 📌 Fitur Utama

- **Multi-Ticker Support** – 100+ saham US dimodelkan secara terpisah (setiap ticker memiliki model XGBoost terlatih sendiri).
- **Walk-Forward Backtesting** – Validasi performa model dengan simulasi *real-time trading* menggunakan data *out-of-sample* berurutan.
- **Feature Engineering Otomatis** – 15+ fitur teknikal (MA, RSI, Volatilitas, Volume Ratio) dihitung secara *on-the-fly* dari data historis.
- **REST API Cepat** – Endpoint `/predict/{ticker}` mengembalikan prediksi harga **hari berikutnya** dalam < 100 ms.
- **Dashboard Interaktif** – Visualisasi harga aktual vs prediksi, distribusi error, dan metrik evaluasi per ticker.
- **Penyimpanan Model Terpusat** – Model `.pkl` disimpan di storage dan metadata-nya di-*track* di PostgreSQL.

---

## 🏗️ Arsitektur Sistem

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│  PostgreSQL  │
│  Frontend   │◀────│   Backend   │◀────│ (Timescale)  │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   XGBoost   │
                    │   Models    │
                    │ (100+ pkl)  │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │Yahoo Finance│
                    │(Data Harian)│
                    └─────────────┘
```

1. **Frontend (Next.js)** – Mengonsumsi API untuk menampilkan prediksi dan riwayat.
2. **Backend (FastAPI)** – Menangani request, mengambil data pasar terbaru, menghitung fitur, dan menjalankan inferensi model.
3. **Database (PostgreSQL)** – Menyimpan data OHLCV historis, log prediksi, dan *model registry* (nama file, metrik evaluasi, timestamp training).
4. **Model Zoo** – 100+ model XGBoost masing-masing *fine-tuned* untuk satu ticker.

---

## 🧠 Machine Learning Pipeline

### 1. Feature Engineering (Hanya Data Historis)

Setiap fitur dihitung dari data **sampai dengan hari H-1**:

| Fitur | Deskripsi |
|-------|-----------|
| `Prev_Close` | Harga penutupan kemarin |
| `Prev_Volume` | Volume perdagangan kemarin |
| `Prev_High` / `Prev_Low` | Harga tertinggi/terendah kemarin |
| `Return_1d` | Persentase perubahan harga (H-2 → H-1) |
| `MA_5`, `MA_20` | Rata-rata bergerak 5 & 20 hari terakhir |
| `Volatility` | (High - Low) / Close kemarin |
| `Volume_Ratio` | Volume kemarin / rata-rata volume 20 hari |
| `RSI_14` | Relative Strength Index 14 hari |
| `Price_Position` | Posisi harga terhadap MA_5 |

### 2. Strategi Pelatihan Model

- **Data split:** Time-based split (80% data awal untuk *training*, 20% terakhir untuk *testing*).
- **Validasi:** Menggunakan *early stopping* pada metrik **MAE** dengan *eval set* yang juga mengikuti urutan waktu.
- **Hyperparameter** tiap ticker dioptimasi via **Optuna** (100 *trials* per ticker).

Contoh konfigurasi XGBoost final (untuk NVDA):

```python
XGBRegressor(
    n_estimators=2000,
    learning_rate=0.01,
    max_depth=4,
    subsample=0.6,
    colsample_bytree=0.7,
    reg_alpha=0.1,
    reg_lambda=1.0,
    early_stopping_rounds=50,
    eval_metric='mae'
)
```

### 3. Manajemen 100+ Model

- Setiap ticker memiliki file model tersendiri: `models/NVDA_v2.pkl`, `models/AAPL_v2.pkl`, dll.
- Tabel PostgreSQL `model_registry` mencatat: `ticker`, `model_path`, `mae_test`, `r2_test`, `directional_accuracy`, `last_training_date`.
- Backend FastAPI memuat model secara **lazy** (hanya saat ticker diminta) untuk menghemat memori.

---

## 📡 API Endpoint (FastAPI)

### `GET /predict/{ticker}`

Mengembalikan prediksi harga penutupan hari berikutnya berdasarkan data pasar terakhir.

**Response:**
```json
{
  "ticker": "NVDA",
  "last_close": 190.77,
  "predicted_close": 192.45,
  "expected_change_pct": 0.88,
  "model_version": "NVDA_v2",
  "timestamp": "2026-04-17T09:30:00Z"
}
```

### `GET /backtest/{ticker}`

Mengembalikan hasil walk-forward backtest 3 bulan terakhir.

### `GET /tickers`

Mengembalikan daftar semua ticker yang tersedia (100+).

---

## 🖥️ Frontend (Next.js)

Dibangun dengan **Next.js 15** dan **Tailwind CSS**, halaman utama menampilkan:

- **Dropdown pemilih ticker** – searchable, 100+ opsi.
- **Kartu Prediksi Hari Ini** – harga penutupan terakhir, prediksi besok, dan arah pergerakan.
- **Grafik Historis** (Recharts) – membandingkan harga aktual dengan prediksi model selama 3 bulan terakhir.
- **Metrik Evaluasi** – MAE, RMSE, Directional Accuracy untuk ticker terpilih.
- **Mode Gelap / Terang** – otomatis mengikuti preferensi sistem.

---

## 🗄️ Database Schema (PostgreSQL)

```sql
-- Tabel data OHLCV harian (partition by ticker, time-series)
CREATE TABLE stock_daily (
    ticker  VARCHAR(10)  NOT NULL,
    date    DATE         NOT NULL,
    open    DECIMAL,
    high    DECIMAL,
    low     DECIMAL,
    close   DECIMAL,
    volume  BIGINT,
    PRIMARY KEY (ticker, date)
);

-- Tabel log prediksi (untuk audit dan monitoring)
CREATE TABLE prediction_log (
    id               SERIAL PRIMARY KEY,
    ticker           VARCHAR(10),
    request_time     TIMESTAMP,
    last_close       DECIMAL,
    predicted_close  DECIMAL,
    model_version    VARCHAR(20)
);

-- Tabel metadata model
CREATE TABLE model_registry (
    ticker        VARCHAR(10)  PRIMARY KEY,
    model_path    VARCHAR(255),
    mae_test      DECIMAL,
    r2_test       DECIMAL,
    direction_acc DECIMAL,
    trained_until DATE,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

---

## ⚙️ Cara Menjalankan Proyek (Lokal)

### Prasyarat

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (dengan ekstensi TimescaleDB — opsional)
- Docker (opsional)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/us-stock-analytics.git
cd us-stock-analytics
```

### 2. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> Pastikan file model `.pkl` berada di folder `backend/models/`.

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Buka [http://localhost:3000](http://localhost:3000)

### 4. Database

Jalankan migrasi schema (gunakan Alembic atau file SQL yang disediakan):

```bash
psql -U postgres -d stock_db -f schema.sql
```

---

## 📈 Performa Model (Contoh untuk 5 Ticker Utama)

| Ticker | MAE (Test) | Directional Accuracy | Model Version |
|--------|-----------|----------------------|---------------|
| NVDA   | 2.87      | 54.2%                | NVDA_v2       |
| AAPL   | 1.42      | 53.1%                | AAPL_v3       |
| MSFT   | 2.10      | 52.8%                | MSFT_v2       |
| TSLA   | 5.33      | 51.5%                | TSLA_v4       |
| AMZN   | 1.98      | 53.7%                | AMZN_v2       |

> **Catatan:** Directional accuracy > 52% pada data *out-of-sample* sudah menunjukkan sinyal yang dapat diandalkan secara statistik untuk pasar efisien.

---

## 🚧 Roadmap Pengembangan

- [x] 100+ model XGBoost terlatih & tervalidasi
- [x] Integrasi FastAPI + Next.js
- [x] PostgreSQL untuk riwayat prediksi
- [ ] Fitur Portfolio Simulator (paper trading)
- [ ] Notifikasi real-time via WebSocket
- [ ] Penjadwalan retraining otomatis mingguan

---

## 👨‍💻 Kontributor

**Muhammad Aldio Yaspindo** – Lead ML Engineer & Backend Developer

[![Instagram](https://img.shields.io/badge/Instagram-E4405F?logo=instagram&logoColor=white)](https://instagram.com/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)](https://github.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://linkedin.com/)

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **MIT License** – lihat file [LICENSE](LICENSE) untuk detail.