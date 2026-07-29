# SENTIKEN Mobile

Aplikasi mobile untuk **mengumpulkan dan menganalisis sentimen ulasan pengguna**
aplikasi **PLN Mobile** dan **MyPertamina** dari Google Play Store, menggunakan
**TF-IDF** untuk pembobotan kata dan algoritma **K-Nearest Neighbor (K-NN)**
untuk klasifikasi sentimen (positif/negatif, opsional netral).

> Proyek ini adalah implementasi rekayasa perangkat lunak dari metodologi
> penelitian tugas akhir "Analisis Sentimen Berdasarkan Ulasan Pengguna Aplikasi
> PLN Mobile dan MyPertamina pada Google Play Store dengan Metode Algoritma
> K-Nearest Neighbor". **Tidak ada data ulasan sintetis** yang dipakai sebagai
> data penelitian — seluruh ulasan berasal dari scraping Google Play Store yang
> sesungguhnya atau import CSV yang diunggah pengguna. Lihat
> [docs/assumptions.md](docs/assumptions.md) untuk daftar keputusan teknis.

## Daftar Isi

- [Fitur](#fitur)
- [Arsitektur](#arsitektur)
- [Struktur Folder](#struktur-folder)
- [Kebutuhan Perangkat](#kebutuhan-perangkat)
- [Instalasi & Konfigurasi](#instalasi--konfigurasi)
- [Menjalankan dengan Docker](#menjalankan-dengan-docker)
- [Menjalankan Manual (tanpa Docker)](#menjalankan-manual-tanpa-docker)
- [Membuat Akun Admin](#membuat-akun-admin)
- [Menjalankan Expo (Mobile)](#menjalankan-expo-mobile)
- [Menjalankan Test](#menjalankan-test)
- [Alur Penggunaan](#alur-penggunaan)
- [Troubleshooting](#troubleshooting)
- [Dokumentasi Lengkap](#dokumentasi-lengkap)

## Fitur

- Manajemen sumber aplikasi (app source) dengan package ID yang dapat diedit.
- Pengumpulan ulasan Google Play Store (scraping) dengan rate limiting, retry,
  progress tracking, dan pembatalan job.
- Import ulasan dari CSV dengan preview, validasi, dan deduplikasi.
- Deduplikasi ulasan berbasis `review_id` atau fingerprint deterministik.
- Pipeline preprocessing teks bahasa Indonesia: case folding, cleaning,
  normalisasi kata tidak baku, tokenizing, stopword removal (dengan
  pengecualian kata negasi), dan stemming (Sastrawi).
- Manajemen kamus (positif, negatif, normalisasi, stopword) dengan
  CRUD, pencarian, dan import/export CSV.
- Labelisasi sentimen berbasis kamus (binary & ternary mode).
- Split data latih/uji (stratified, dengan validasi kelayakan).
- Pembobotan TF-IDF dan klasifikasi K-Nearest Neighbor, termasuk eksperimen
  multi-nilai K dan aktivasi model dengan konfirmasi eksplisit.
- Evaluasi lengkap: accuracy, precision, recall, F1-score, confusion matrix,
  classification report.
- Prediksi sentimen untuk satu teks ulasan beserta tetangga terdekat.
- Dashboard ringkasan, perbandingan sentimen antar aplikasi, tren, dan term
  frekuensi tertinggi (murni dari data yang ada, tanpa klaim tanpa dasar data).
- Ekspor CSV (raw/preprocessing/labeling/train/test/predictions/metrics),
  confusion matrix PNG, dan ringkasan PDF.
- Autentikasi admin tunggal berbasis JWT (access + refresh token).

## Arsitektur

```
┌─────────────────┐      HTTPS/JSON       ┌──────────────────┐
│  Mobile (Expo)   │  ───────────────────▶ │  FastAPI Backend  │
│  React Native    │ ◀─────────────────── │  (REST /api/v1)   │
└─────────────────┘                       └────────┬─────────┘
                                                     │ SQLAlchemy
                                            ┌────────▼─────────┐
                                            │   PostgreSQL      │
                                            └────────────────────┘
                                                     │
                                            ┌────────▼─────────┐
                                            │  Redis (opsional)│
                                            │  + RQ worker      │
                                            └────────────────────┘
```

Backend menjalankan job berat (scraping, import, preprocessing, labelisasi,
training) di background. Mode `JOB_EXECUTION_MODE=inline` menjalankannya pada
thread pool lokal (tanpa Redis, cocok untuk development/testing). Mode
`JOB_EXECUTION_MODE=rq` mengirim job ke antrean Redis yang dikonsumsi oleh
container `worker` terpisah (direkomendasikan untuk penggunaan yang lebih berat).

## Struktur Folder

```
sentiken-mobile/
├── mobile/                # Aplikasi Expo React Native (TypeScript)
├── backend/                # FastAPI + SQLAlchemy + Alembic + ML pipeline
│   ├── app/
│   │   ├── api/v1/         # Endpoint REST
│   │   ├── models/         # Model SQLAlchemy
│   │   ├── schemas/        # Skema Pydantic
│   │   ├── services/       # Logika bisnis & ML pipeline
│   │   ├── jobs/           # Antrean background job
│   │   └── workers/        # Entry point worker RQ
│   ├── alembic/             # Migration database
│   ├── scripts/             # create_admin, seed_reference_data
│   ├── tests/                # Pytest (unit + integration)
│   └── storage/              # Model joblib & file ekspor (runtime)
├── docs/                    # Dokumentasi tambahan
├── scripts/                  # Skrip bantu di level monorepo (opsional)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Kebutuhan Perangkat

- Docker Desktop / Docker Engine + Docker Compose v2 (jalur tercepat)
- **Atau**, untuk menjalankan manual:
  - Python 3.12+
  - PostgreSQL 14+ (atau SQLite untuk testing backend saja)
  - Redis 7+ (opsional, hanya untuk mode job `rq`)
  - Node.js 20+ dan npm/pnpm untuk aplikasi mobile
  - Expo Go (Android/iOS) atau emulator Android Studio / Xcode Simulator

## Instalasi & Konfigurasi

1. Clone/unduh proyek ini, lalu masuk ke direktori `sentiken-mobile/`.
2. Salin file environment:
   ```bash
   cp .env.example .env
   ```
3. Sesuaikan nilai di `.env`, terutama:
   - `ADMIN_EMAIL` dan `ADMIN_PASSWORD` (akun admin tunggal, **wajib diganti**).
   - `JWT_SECRET_KEY` (gunakan string acak yang panjang).
   - `POSTGRES_PASSWORD`.
   - `PLN_MOBILE_PACKAGE_ID` / `MYPERTAMINA_PACKAGE_ID` (boleh dikosongkan,
     dapat diisi/diedit lewat aplikasi mobile setelah berjalan).

## Menjalankan dengan Docker

```bash
docker compose up --build
```

Perintah ini akan:
1. Menjalankan PostgreSQL dan Redis dengan healthcheck.
2. Menjalankan migration Alembic secara otomatis (`alembic upgrade head`).
3. Membuat/memperbarui akun admin dari `.env` (`scripts/create_admin.py`).
4. Mengisi data referensi awal (app sources PLN Mobile & MyPertamina, kamus
   starter) via `scripts/seed_reference_data.py` — **tanpa data ulasan**.
5. Menjalankan backend FastAPI di `http://localhost:8000` (dokumentasi API di
   `http://localhost:8000/docs`).
6. Menjalankan container `worker` yang mengonsumsi antrean job Redis.

Untuk menjalankan pgAdmin (opsional):
```bash
docker compose --profile tools up -d pgadmin
```
Akses di `http://localhost:5050`.

Menghentikan seluruh service:
```bash
docker compose down
```

Menghapus juga volume data (reset total):
```bash
docker compose down -v
```

## Menjalankan Manual (tanpa Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# .venv\Scripts\activate.bat    # Windows CMD
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements-dev.txt
```

Siapkan PostgreSQL lokal, lalu set `DATABASE_URL` pada `.env` atau environment,
contoh:
```
DATABASE_URL=postgresql+psycopg2://sentiken:password@localhost:5432/sentiken
```

Jalankan migration:
```bash
python -m alembic upgrade head
```

Buat akun admin dan isi data referensi awal:
```bash
python -m scripts.create_admin
python -m scripts.seed_reference_data
```

Jalankan backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Worker (opsional, hanya jika `JOB_EXECUTION_MODE=rq`)

Jalankan Redis lokal, lalu:
```bash
cd backend
source .venv/Scripts/activate
python -m app.workers.worker
```

Jika `JOB_EXECUTION_MODE=inline` (default rekomendasi untuk development tanpa
Redis), worker terpisah tidak diperlukan — job berjalan pada thread pool
backend itu sendiri.

## Membuat Akun Admin

Akun admin **tidak pernah di-hardcode**. Kredensial selalu dibaca dari
environment variable `ADMIN_EMAIL` dan `ADMIN_PASSWORD`. Skrip
`scripts/create_admin.py` bersifat idempoten — aman dijalankan berulang kali
(akan memperbarui kata sandi bila sudah ada).

## Menjalankan Expo (Mobile)

```bash
cd mobile
npm install
cp .env.example .env    # sesuaikan EXPO_PUBLIC_API_URL
npx expo start
```

- Scan QR code dengan aplikasi **Expo Go** (Android/iOS) di jaringan yang sama.
- Atau tekan `a` untuk membuka emulator Android / `i` untuk simulator iOS.
- Set `EXPO_PUBLIC_API_URL` sesuai target:
  - Emulator Android: `http://10.0.2.2:8000/api/v1`
  - Simulator iOS: `http://localhost:8000/api/v1`
  - Device fisik (Expo Go, jaringan sama): `http://<IP-LAN-komputer>:8000/api/v1`

## Menjalankan Test

### Backend

```bash
cd backend
source .venv/Scripts/activate
pytest                     # seluruh test
pytest --cov=app           # dengan coverage
ruff check app/ scripts/ tests/
black --check app/ scripts/ tests/
```

Test backend memakai **SQLite berbasis file** (bukan PostgreSQL) sesuai
batasan "SQLite hanya untuk testing backend" pada spesifikasi proyek — lihat
`tests/conftest.py`.

### Mobile

```bash
cd mobile
npm test
npm run lint
```

## Alur Penggunaan

1. **Login** dengan akun admin.
2. Buka menu **Sumber Aplikasi**, lengkapi/verifikasi `package_id` PLN Mobile
   dan MyPertamina (atau tambah sumber baru).
3. Buat **Dataset** baru terkait sumber aplikasi tersebut.
4. Di menu **Proses → Pengumpulan Data**, jalankan scraping (tentukan periode,
   maksimal ulasan, bahasa, negara) — atau gunakan **Import CSV** sebagai
   alternatif/fallback.
5. Jalankan **Preprocessing**.
6. Kelola **Kamus** (positif/negatif/normalisasi/stopword) sesuai kebutuhan,
   lalu jalankan **Labelisasi** (pilih mode binary/ternary).
7. Jalankan **Split Data**, lalu **Latih Model** (TF-IDF + K-NN) atau
   **Eksperimen K** untuk membandingkan beberapa nilai K.
8. Lihat **Hasil Evaluasi** (confusion matrix, accuracy/precision/recall/F1).
9. Aktifkan model (butuh konfirmasi bila menggantikan model aktif lain).
10. Gunakan **Prediksi Satu Teks** untuk menguji ulasan baru.
11. Lihat **Dashboard** dan **Perbandingan Aplikasi** untuk ringkasan analisis.
12. **Ekspor** hasil (CSV/PNG/PDF) sesuai kebutuhan dokumentasi penelitian.

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `docker compose up` gagal saat migration | Pastikan container `postgres` sudah *healthy* (`docker compose ps`); tunggu healthcheck selesai. |
| Backend tidak bisa konek DB saat manual run | Periksa `DATABASE_URL`; pastikan PostgreSQL berjalan dan kredensial cocok dengan `.env`. |
| Login gagal padahal kredensial benar | Jalankan ulang `python -m scripts.create_admin` untuk memastikan admin tersinkron dengan `.env` terbaru. |
| Scraping gagal / package tidak ditemukan | Verifikasi `package_id` lewat menu Sumber Aplikasi → Validasi, atau cek koneksi internet. Gunakan Import CSV sebagai fallback. |
| Mobile tidak bisa akses backend | Pastikan `EXPO_PUBLIC_API_URL` menunjuk ke alamat yang bisa dijangkau perangkat (lihat catatan emulator/device fisik di atas). |
| Training gagal "Nilai K lebih besar dari data training" | Kurangi nilai K atau perbesar proporsi data training saat split. |
| Split gagal "stratified split tidak dapat dijalankan" | Kelas dengan data terlalu sedikit; kumpulkan/label lebih banyak data, atau nonaktifkan stratify (memahami risikonya). |
| Redis tidak tersedia padahal `JOB_EXECUTION_MODE=rq` | Backend otomatis fallback menjalankan job secara inline dan mencatat warning di log; pastikan container `redis` berjalan untuk performa produksi. |

## Dokumentasi Lengkap

- [docs/database.md](docs/database.md) — skema database & relasi.
- [docs/api.md](docs/api.md) — ringkasan endpoint REST API.
- [docs/ml-pipeline.md](docs/ml-pipeline.md) — detail pipeline preprocessing, TF-IDF, K-NN, evaluasi.
- [docs/mobile-screens.md](docs/mobile-screens.md) — daftar layar mobile & alurnya.
- [docs/deployment.md](docs/deployment.md) — panduan deployment.
- [docs/assumptions.md](docs/assumptions.md) — asumsi & keputusan teknis atas ketidakjelasan spesifikasi.
- [docs/progress.md](docs/progress.md) — catatan progres per tahap implementasi.
- [docs/contoh-format-import-csv.csv](docs/contoh-format-import-csv.csv) — contoh format kolom CSV (bukan data penelitian).
- [CLAUDE.md](CLAUDE.md) — panduan kerja untuk kontributor/asisten AI di repo ini.
