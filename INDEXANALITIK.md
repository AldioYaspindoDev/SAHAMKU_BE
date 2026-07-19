# 📈 Indonesia Stock Index Analytics

## Tujuan

Membangun platform analitik historis indeks saham Indonesia seperti:

- LQ45
- IDX30
- IDX80
- Kompas100
- Sri-Kehati
- ESG Leaders
- Bisnis-27
- PEFINDO25
- BUMN20
- dan indeks lainnya.

Platform ini **bukan untuk trading**, tetapi memberikan insight berdasarkan data historis indeks selama bertahun-tahun.

---

# Level 1 — Basic Analytics

Analitik dasar yang wajib dimiliki.

## 1. Frequency Analysis

Menghitung berapa kali suatu emiten muncul pada indeks.

Output:

|Kode|Kemunculan|
|---|---:|
|BBCA|20|
|BBRI|20|
|ANTM|13|

Formula

Frequency = Jumlah Periode Muncul

---

## 2. Longest Streak

Menghitung berapa lama emiten bertahan berturut-turut.

Output

BBCA

████████████████

20 periode

ANTM

████
███

Longest = 4

---

## 3. Entry Count

Menghitung berapa kali emiten pertama kali masuk.

Contoh

2018

Masuk

ANTM

2020

Masuk Lagi

ANTM

Entry Count = 2

---

## 4. Exit Count

Menghitung berapa kali keluar dari indeks.

Output

ANTM

Exit = 2

---

## 5. Re-entry Count

Menghitung berapa kali keluar lalu berhasil masuk kembali.

Output

ANTM

Re-entry = 2

---

## 6. Survival Rate

Menghitung persentase bertahan.

Misalnya

20 periode

Muncul 18

Survival

90%

Formula

Survival Rate = Frequency / Total Periode

---

# Level 2 — Weight Analytics

Menggunakan data bobot indeks.

## 7. Average Weight

Rata-rata bobot selama seluruh periode.

Formula

Average Weight =
Σ Bobot / Jumlah Periode

---

## 8. Maximum Weight

Bobot terbesar yang pernah dicapai.

---

## 9. Minimum Weight

Bobot terkecil.

---

## 10. Weight Growth

Perubahan bobot dari periode pertama hingga terakhir.

Formula

(Current - First)/First

---

## 11. Weight Stability

Menggunakan Standard Deviation.

Semakin kecil

↓

Semakin stabil.

Formula

Std(Bobot)

---

## 12. Weight Trend

Menentukan

- Naik
- Turun
- Stabil

Menggunakan Linear Regression sederhana.

Output

BBCA

📈 Increasing

---

## 13. Weight Rank

Ranking bobot setiap periode.

Output

2022

1 BBCA

2 BBRI

3 BMRI

---

# Level 3 — Index Dynamics

Melihat perubahan isi indeks.

## 14. Turnover Rate

Berapa banyak anggota berubah setiap evaluasi.

Formula

Jumlah Entry + Exit

---

## 15. Retention Rate

Persentase anggota yang tetap bertahan.

Formula

Remaining / Previous Members

---

## 16. New Members

Daftar perusahaan baru.

---

## 17. Removed Members

Daftar perusahaan yang keluar.

---

## 18. Timeline

Menampilkan histori perubahan.

2021

+ BRPT

- PGAS

2022

+ ANTM

- WIKA

---

# Level 4 — Consistency Analytics

Insight utama aplikasi.

## 19. Consistency Score

Skor berdasarkan

- Frequency
- Longest Streak
- Weight Stability
- Average Weight
- Exit Rate

Formula

Score =
30% Frequency
30% Streak
20% Stability
20% Weight

Output

BBCA

98

---

## 20. Index Elite

Top 10 perusahaan paling konsisten.

Output

1 BBCA

2 BBRI

3 BMRI

---

## 21. Stable vs Volatile

Klasifikasi

Stable

Moderate

Volatile

---

## 22. Hall of Fame

Perusahaan yang

- tidak pernah keluar
- streak terpanjang
- survival tertinggi

---

# Level 5 — Dashboard

## Ringkasan

Jumlah Periode

Jumlah Emiten Unik

Rata-rata Pergantian Anggota

Top Consistency

Top Weight

---

## Charts

- Frequency Bar Chart
- Weight Trend
- Entry Exit Timeline
- Heatmap
- Consistency Ranking
- Turnover Chart

---

# Data Model

Index

- id
- name

Period

- id
- year
- semester
- evaluation_date

Constituent

- period_id
- stock_code
- weight
- free_float
- shares
- status

Analytics

- stock_code
- frequency
- longest_streak
- entry_count
- exit_count
- reentry_count
- survival_rate
- average_weight
- max_weight
- min_weight
- weight_std
- consistency_score

---

# Python Modules

project/

loader.py

Membaca seluruh Excel.

---

cleaner.py

Membersihkan data.

---

builder.py

Menggabungkan seluruh periode.

---

analytics/

frequency.py

streak.py

weight.py

turnover.py

consistency.py

timeline.py

ranking.py

---

visualization.py

Membuat grafik.

---

export.py

Ekspor JSON untuk API.

---

main.py

Menjalankan seluruh pipeline.