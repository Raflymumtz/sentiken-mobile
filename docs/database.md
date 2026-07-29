# Skema Database

Database utama: **PostgreSQL** (produksi/dev). **SQLite** hanya dipakai untuk
test suite backend (`tests/conftest.py`). Migration dikelola oleh **Alembic**
(`backend/alembic/`). Semua tabel memakai **UUID primary key**, kolom
`created_at`/`updated_at` (kecuali tabel log/hasil yang immutable), dan
soft-delete (`deleted_at`) khusus pada `app_sources` & `datasets`.

## Daftar Tabel

| Tabel | Deskripsi |
|---|---|
| `users` | Akun admin (single-user research tool). |
| `app_sources` | Sumber aplikasi (PLN Mobile, MyPertamina, dst) — `package_id` unik. |
| `datasets` | Kumpulan ulasan per sumber aplikasi + status pipeline. |
| `reviews` | Ulasan pengguna. Unik pada `(app_source_id, review_id)`. |
| `preprocessing_results` | Hasil tiap tahap preprocessing per review (1:1). |
| `sentiment_labels` | Hasil labelisasi kamus per review per `label_mode` (1:n review). |
| `dictionary_positive` | Kamus kata positif (`word` unik, `weight`). |
| `dictionary_negative` | Kamus kata negatif (`word` unik, `weight`). |
| `normalization_dictionary` | Kamus normalisasi (`informal_word` unik → `formal_word`). |
| `stopwords` | Daftar stopword (`word` unik). |
| `data_splits` | Konfigurasi & hasil split train/test (daftar ID direproduksi). |
| `training_runs` | Training run tunggal atau eksperimen-K + status + config. |
| `training_run_items` | Hasil per nilai K dalam satu eksperimen. |
| `tfidf_models` | Metadata + path joblib model TF-IDF per training run. |
| `knn_models` | Metadata + path joblib model K-NN per training run. |
| `predictions` | Hasil prediksi (evaluasi batch maupun prediksi satu teks). |
| `evaluation_metrics` | Metrik evaluasi (confusion matrix, classification report, dst). |
| `collection_jobs` | Job pengumpulan data dari Google Play Store + progress. |
| `import_jobs` | Job import CSV + laporan validasi. |
| `audit_logs` | Log aktivitas admin (tanpa password/token). |

## Relasi Utama

```
app_sources 1───n datasets
datasets    1───n reviews
reviews     1───1 preprocessing_results
reviews     1───n sentiment_labels        (satu per label_mode)
datasets    1───n data_splits
datasets    1───n training_runs
training_runs 1───1 tfidf_models
training_runs 1───1 knn_models
training_runs 1───n training_run_items    (khusus run_type="experiment")
training_runs 1───n evaluation_metrics
training_runs 1───n predictions
datasets    1───n collection_jobs
datasets    1───n import_jobs
```

## Index & Constraint Penting

- `reviews`: unique `(app_source_id, review_id)`; index pada `review_date`,
  `dataset_id`, `app_source_id`, `fingerprint`.
- `sentiment_labels`: index pada `review_id`, `dataset_id`, `label`.
- `app_sources.package_id`: unique + index.
- `users.email`: unique + index.
- Foreign key `reviews.app_source_id` memakai `ondelete=RESTRICT` (sumber
  aplikasi tidak bisa dihapus permanen selama masih punya ulasan — sejalan
  dengan soft-delete pada `app_sources`).
- Foreign key `reviews.dataset_id`, `sentiment_labels.*`, `predictions.*`
  memakai `ondelete=CASCADE` agar konsisten saat dataset/training run dihapus.

## Tipe UUID Lintas Database

Kolom UUID memakai tipe kustom `GUID`
(`backend/app/models/types.py`) yang otomatis memetakan ke tipe `UUID` native
PostgreSQL, atau `CHAR(32)` (hex) pada SQLite — sehingga model yang sama bisa
dipakai untuk database produksi maupun test suite tanpa duplikasi kode.

## Menjalankan Migration

```bash
cd backend
python -m alembic upgrade head        # terapkan migration terbaru
python -m alembic downgrade -1        # rollback satu langkah
python -m alembic revision --autogenerate -m "pesan"   # migration baru
```
