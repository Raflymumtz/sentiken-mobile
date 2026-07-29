# Catatan Progres Implementasi

Status per tahap sesuai rencana implementasi bertahap. Diperbarui seiring
pengerjaan — lihat riwayat commit untuk detail kronologis.

## Tahap 1 — Struktur Monorepo, Docker, Skeleton

**Status: selesai.**
- Struktur folder monorepo (`mobile/`, `backend/`, `docs/`, `scripts/`).
- `.env.example` lengkap dengan seluruh variabel yang dipakai backend, worker,
  dan mobile.
- `docker-compose.yml`: `postgres`, `redis`, `backend`, `worker`, `pgadmin`
  (profile `tools`), dengan healthcheck & volume persisten.
- Backend skeleton FastAPI berjalan (`/health`, OpenAPI docs).

## Tahap 2 — Database, Migration, Autentikasi, CRUD Dasar

**Status: selesai.**
- 20 model SQLAlchemy (lihat [docs/database.md](database.md)) + migration
  Alembic awal (upgrade & downgrade diverifikasi pada SQLite).
- Autentikasi JWT (access + refresh, rotasi, revocation) dengan akun admin
  dari environment variable (`scripts/create_admin.py`).
- CRUD sumber aplikasi (dengan validasi format package ID + cek keberadaan
  di Play Store) dan dataset (dengan soft delete).
- Test: `test_auth.py`, `test_app_sources.py`, `test_datasets.py`.

## Tahap 3 — Pengumpulan Data, Import CSV, Deduplikasi, Background Job

**Status: selesai.**
- Scraping Google Play Store (`google-play-scraper`) dengan retry (tenacity),
  jeda antar-request, filter periode, pagination, dan dukungan pembatalan job.
- Import CSV dua tahap (preview → execute) dengan validasi kolom/tipe data,
  laporan baris valid/tidak valid, dan transaksi database.
- Deduplikasi berbasis `review_id` atau fingerprint SHA-256 deterministik.
- Background job dua mode: `inline` (thread pool) dan `rq` (Redis + worker),
  dengan fallback otomatis bila Redis tidak tersedia.
- Test: `test_collection_jobs.py`, `test_imports.py`, `test_dedup.py`.

## Tahap 4 — Preprocessing, Kamus, Labelisasi

**Status: selesai.**
- Pipeline 7 tahap (case folding → cleaning → normalisasi → tokenizing →
  stopword removal → stemming → final text), kata negasi selalu dipertahankan.
- CRUD kamus (positif/negatif/normalisasi/stopword) + import/export CSV +
  validasi duplikat.
- Labelisasi kamus sentimen (binary & ternary mode) sesuai rumus penelitian.
- Test: `test_preprocessing.py`, `test_preprocessing_api.py`,
  `test_dictionaries.py`, `test_labeling.py`.

## Tahap 5 — Split, TF-IDF, K-NN, Evaluasi, Prediksi

**Status: selesai.**
- Split data dengan validasi kelayakan stratified split (gagal eksplisit +
  alasan, bukan fallback diam-diam).
- TF-IDF (`TfidfVectorizer`, fit hanya pada data training) & K-NN
  (`KNeighborsClassifier`, Euclidean distance) — training tunggal & eksperimen
  multi-K dengan pemilihan model terbaik otomatis (rekomendasi, bukan
  aktivasi otomatis).
- Aktivasi model dengan konfirmasi eksplisit (kecuali training run pertama
  pada dataset yang belum punya model aktif).
- Evaluasi lengkap (confusion matrix, classification report, metrik macro &
  weighted, `zero_division=0` + warning).
- Prediksi satu teks + daftar tetangga terdekat.
- Test: `test_split.py`, `test_training.py`, `test_evaluation_service.py`,
  `test_predictions.py`.

## Tahap 5b — Dashboard, Perbandingan, Ekspor

**Status: selesai.**
- Dashboard summary, perbandingan sentimen antar aplikasi, tren, distribusi
  rating, term frekuensi tertinggi — seluruhnya dari data nyata (empty state
  eksplisit bila belum ada data).
- Ekspor CSV (raw/preprocessing/labeling/train/test/predictions/metrics/
  classification report), PNG confusion matrix (Pillow), PDF ringkasan
  (ReportLab).
- Test: `test_dashboard.py`, `test_export.py`.

## Backend — Ringkasan Kualitas

- **97 test** lulus (`pytest`), mencakup seluruh area wajib pada spesifikasi
  bagian 9 (auth, CRUD, import, dedup, preprocessing, normalisasi, stopword,
  stemming, labelisasi binary/ternary, split, TF-IDF, K-NN, evaluasi, prediksi
  satu teks, empty dataset, dataset satu kelas, CSV rusak, job gagal, unique
  constraint).
- `ruff check` & `black --check` bersih tanpa error.
- `alembic check` — tidak ada drift antara model dan migration.
- **Belum dijalankan** (keterbatasan sandbox pengembangan tanpa Docker):
  `docker compose up --build` end-to-end pada Postgres/Redis sungguhan. Model
  divalidasi lewat SQLite (sesuai batasan spesifikasi untuk testing) dan
  struktur `docker-compose.yml` divalidasi secara sintaksis (YAML parse).

## Tahap 6 — Mobile App

**Status: selesai (kode lengkap, belum diverifikasi dengan runtime Expo — lihat catatan di bawah).**
- Expo Router + TypeScript, 5 bottom tab (Dashboard, Dataset, Proses, Analisis,
  Pengaturan), total 24 layar mencakup seluruh fitur A–Q pada spesifikasi:
  login, dashboard (stat + grafik), CRUD sumber aplikasi, CRUD dataset,
  pengumpulan data (job + progress + cancel), import CSV (preview → execute),
  daftar & detail ulasan (7 tahap preprocessing, skor label, tetangga
  terdekat), 4 menu kamus (CRUD + import/export CSV), preprocessing,
  labelisasi (binary/ternary), split data, training + eksperimen-K, aktivasi
  model (dengan konfirmasi), evaluasi (confusion matrix, metrik, ekspor
  PNG/PDF/CSV), prediksi satu teks, perbandingan aplikasi (chart + term
  frekuensi), pengaturan tema & akun.
- State: TanStack Query untuk seluruh data server (dengan polling status job
  otomatis), Zustand untuk sesi auth (tersinkron `expo-secure-store`) dan
  preferensi UI, React Hook Form + Zod untuk validasi form.
- Komponen bersama konsisten (loading/empty/error state, confirmation dialog,
  toast, badge status, progress bar) memenuhi kebutuhan UI/UX spesifikasi.
- Test Jest + React Native Testing Library: login (validasi & sukses),
  dashboard (loading/empty/error tanpa metrik palsu), daftar dataset, form
  pengumpulan data, validasi import CSV, form training, tampilan evaluasi,
  serta refresh token saat kedaluwarsa.

**Catatan keterbatasan verifikasi**: sandbox pengembangan yang dipakai tidak
memiliki Node.js/npm, sehingga `npm install`, `expo start`, `npm run
typecheck`, `npm run lint`, dan `npm test` belum bisa benar-benar dieksekusi
di lingkungan tersebut. Seluruh kode ditulis dan ditinjau ulang secara manual
(struktur import, path routing, penamaan komponen) mengikuti konvensi Expo
Router v4 yang baku, tetapi **belum dijalankan langsung**. Jalankan langkah
verifikasi di [docs/mobile-screens.md](mobile-screens.md#keterbatasan-verifikasi)
sebelum menganggap bagian mobile final.

## Tahap 7 — Testing, Lint, Dokumentasi Final

**Status: selesai untuk backend, tertunda untuk mobile** (menunggu
verifikasi `npm install`/`expo start` di lingkungan dengan Node.js — lihat
catatan Tahap 6). Test & lint backend dijalankan setelah setiap tahap
(bukan ditunda ke akhir); seluruhnya hijau (97 test, ruff, black, alembic
check). Dokumentasi (`docs/*.md`, `README.md`, `CLAUDE.md`) ditulis mengikuti
implementasi masing-masing tahap agar tetap akurat.
