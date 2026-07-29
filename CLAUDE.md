# CLAUDE.md

Panduan kerja untuk siapa pun (manusia atau asisten AI) yang mengembangkan
proyek **SENTIKEN Mobile** di repo ini.

## Aturan Struktur Proyek

- `backend/` — FastAPI + SQLAlchemy + Alembic + pipeline ML. Kode aplikasi di
  `backend/app/`, terbagi: `api/v1/` (route), `models/` (ORM), `schemas/`
  (Pydantic), `services/` (logika bisnis/ML, tidak boleh bergantung pada
  FastAPI), `jobs/` (antrean background), `workers/` (entry point RQ worker).
- `mobile/` — Expo React Native + TypeScript. Struktur route di `app/`
  (Expo Router), komponen dapat dipakai ulang di `components/`, state di
  `store/` (Zustand), API client di `lib/api/`.
- `docs/` — dokumentasi tambahan (database, API, ML pipeline, layar mobile,
  deployment, asumsi, progres).
- Jangan menaruh logika bisnis di layer route (`api/v1/*.py`) — route hanya
  boleh: validasi request via Pydantic, panggil service, bentuk response.
- Jangan menaruh query database langsung di komponen mobile — selalu lewat
  `lib/api/` + TanStack Query hooks.

## Perintah Lint & Test

**Backend** (dari `backend/`, dengan venv aktif):
```bash
pytest                                   # jalankan semua test
pytest --cov=app                          # dengan coverage
ruff check app/ scripts/ tests/            # lint
black app/ scripts/ tests/                  # format
python -m alembic check                      # cek drift migration vs model
```

**Mobile** (dari `mobile/`):
```bash
npm test
npm run lint
npx tsc --noEmit
```

Sebelum menandai suatu pekerjaan "selesai", **kedua** perintah test dan lint
di atas harus lulus tanpa error (warning boleh, tapi harus dicatat bila
disengaja).

## Larangan Data Sintetis untuk Hasil Penelitian

- **Jangan pernah** menambahkan/mengembalikan data ulasan yang seolah-olah
  berasal dari Google Play Store tapi sebenarnya direkayasa. Data ulasan
  hanya boleh berasal dari scraping sungguhan (`app/services/scraping.py`)
  atau import CSV yang diunggah pengguna.
- **Jangan pernah** mengarang/menghardcode accuracy, precision, recall,
  F1-score, confusion matrix, atau jumlah data apa pun di response API,
  dashboard, atau dokumen ekspor. Semua metrik **wajib** dihitung dari data
  yang benar-benar ada (lihat `app/services/evaluation_service.py`).
- Data uji (test fixture) di `backend/tests/` **wajib** diberi label jelas
  sebagai `TEST FIXTURE` di docstring/komentar, dan tidak boleh dipakai atau
  disalin sebagai contoh data penelitian di dokumentasi lain.
- Kamus starter (`app/data/seed_dictionary.py`) adalah titik awal yang wajar,
  bukan leksikon final — jangan mempresentasikannya sebagai leksikon yang
  sudah tervalidasi secara akademis tanpa peninjauan pengguna.

## Konvensi API

- Semua endpoint di bawah prefix `/api/v1`.
- Response list selalu paginated: `{ "items": [...], "pagination": {...} }`.
- Response error selalu: `{ "error": { "code", "message", "fields?" } }`
  (lihat `app/core/errors.py`).
- Endpoint yang butuh auth memakai dependency `get_current_user`
  (`app/api/deps.py`) — jangan implementasi ulang pengecekan token secara manual.
- Job berat (scraping, import, preprocessing, labelisasi, training) **wajib**
  dijalankan via `app/jobs/queue.py: submit_job()`, bukan langsung di handler
  request (agar request tidak blocking dan konsisten dengan mode
  inline/RQ).
- Teks antarmuka yang dikirim ke klien (pesan error, label) berbahasa
  Indonesia. Nama variabel & fungsi tetap bahasa Inggris.

## Konvensi Database

- Semua tabel: UUID primary key, `created_at`/`updated_at` (kecuali tabel
  log/hasil immutable seperti `predictions`, `evaluation_metrics`).
- Soft delete (`deleted_at`) hanya untuk `app_sources` dan `datasets` — jangan
  tambahkan soft delete ke tabel lain tanpa alasan kuat (menambah kompleksitas
  query di semua tempat).
- Setiap perubahan model **wajib** disertai migration Alembic
  (`python -m alembic revision --autogenerate -m "..."`), dan jalankan
  `python -m alembic check` untuk memastikan tidak ada drift.
- Tipe UUID lintas dialek memakai `app.models.types.GUID` — jangan pakai
  `sqlalchemy.dialects.postgresql.UUID` langsung di model (akan merusak
  kompatibilitas SQLite test suite).
- Relasi antar model lintas file **jangan** saling mengimpor langsung di
  top-level (berisiko circular import) — gunakan `Mapped["ClassName"]` dengan
  string forward-reference, dan tambahkan import di bawah blok
  `if TYPE_CHECKING:` untuk keperluan analisis statis. Registrasi runtime
  seluruh model terjadi lewat `app/models/__init__.py`.

## Konvensi Komponen Mobile

- Gunakan Expo Router untuk navigasi (file-based routing di `mobile/app/`).
- State server (data dari API) selalu lewat TanStack Query — jangan simpan
  hasil fetch API di Zustand. Zustand hanya untuk state klien murni (auth
  token, preferensi UI seperti dark mode).
- Form memakai React Hook Form + Zod (skema validasi Zod ditaruh berdekatan
  dengan komponen form atau di `lib/validation/`).
- Semua teks yang terlihat pengguna berbahasa Indonesia.
- Tampilkan **empty state** eksplisit ketika data kosong — jangan tampilkan
  angka 0/placeholder yang bisa disalahartikan sebagai hasil sungguhan.

## Langkah Verifikasi Sebelum Menyatakan Pekerjaan Selesai

1. `cd backend && pytest` — semua test lulus.
2. `cd backend && ruff check app/ scripts/ tests/ && black --check app/ scripts/ tests/` — bersih.
3. `cd backend && python -m alembic check` — tidak ada drift migration.
4. `cd mobile && npm run lint && npx tsc --noEmit && npm test` — bersih & lulus.
5. Jalankan `docker compose up --build` dan pastikan backend healthy serta
   migration/seed berjalan tanpa error (bila lingkungan punya Docker).
6. Update `docs/progress.md` dengan status tahap yang baru diselesaikan.
7. Jangan menyatakan pekerjaan selesai bila salah satu langkah di atas gagal.
