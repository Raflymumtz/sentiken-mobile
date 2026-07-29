# Ringkasan API

Base URL: `http://localhost:8000/api/v1`. Dokumentasi interaktif (OpenAPI/Swagger)
tersedia otomatis di `http://localhost:8000/docs` dan `/redoc` saat backend
berjalan. Seluruh endpoint (kecuali `/auth/login`, `/auth/refresh`, dan
`/health`) memerlukan header `Authorization: Bearer <access_token>`.

## Format Response

**Sukses (list, paginated):**
```json
{ "items": [ ... ], "pagination": { "page": 1, "page_size": 20, "total_items": 42, "total_pages": 3 } }
```

**Error:**
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "fields": { "field": "pesan" } } }
```

## Autentikasi

| Method | Path | Keterangan |
|---|---|---|
| POST | `/auth/login` | Login, mengembalikan access + refresh token. |
| POST | `/auth/refresh` | Rotasi refresh token → access token baru. |
| POST | `/auth/logout` | Revoke refresh token. |
| GET | `/auth/me` | Profil admin yang sedang login. |

## Sumber Aplikasi

`GET|POST /app-sources`, `GET|PUT|DELETE /app-sources/{id}`,
`POST /app-sources/{id}/validate` (cek keberadaan package ID di Play Store).

## Dataset

`GET|POST /datasets`, `GET|PUT|DELETE /datasets/{id}`,
`GET /datasets/{id}/summary`, `GET /datasets/{id}/reviews` (filter: `label`,
`score`, `date_from`, `date_to`, `search`, `preprocessing_status`,
`prediction_status`), `GET /datasets/{id}/export?kind=raw|preprocessing|labeling`.

## Pengumpulan Data

`POST|GET /collection-jobs`, `GET /collection-jobs/{id}`,
`POST /collection-jobs/{id}/cancel`.

## Import CSV

`POST /datasets/{id}/imports/preview` (multipart file, tidak menyimpan ke DB),
`POST /datasets/{id}/imports/execute` (pakai `upload_token` dari preview),
`GET /import-jobs/{id}`.

## Preprocessing

`POST /datasets/{id}/preprocess`, `GET /datasets/{id}/preprocessing-status`,
`GET /reviews/{id}/preprocessing`, `GET /reviews/{id}` (detail lengkap ulasan).

## Kamus

`GET|POST /dictionaries/{type}` dan `PUT|DELETE /dictionaries/{type}/{id}`
(`type` = `positive|negative|normalization|stopwords`),
`POST /dictionaries/{type}/import` (CSV), `GET /dictionaries/{type}/export` (CSV).

## Labelisasi

`POST /datasets/{id}/label` (`{"label_mode": "binary"|"ternary"}`),
`GET /datasets/{id}/label-summary`.

## Split Data

`POST /datasets/{id}/split`, `GET /datasets/{id}/splits`.

## Training & Model

`POST /datasets/{id}/train`, `POST /datasets/{id}/experiment-k`,
`GET /training-runs` (filter `dataset_id`, `run_type`), `GET /training-runs/{id}`,
`POST /training-runs/{id}/activate` (`{"confirm": true}`).

## Evaluasi

`GET /training-runs/{id}/metrics`, `GET /training-runs/{id}/confusion-matrix`,
`GET /training-runs/{id}/classification-report`, `GET /training-runs/{id}/predictions`.

## Prediksi

`POST /predictions/single` (`{"text": "...", "training_run_id": "opsional"}`),
`GET /predictions/history`.

## Dashboard

`GET /dashboard/summary`, `GET /dashboard/sentiment-comparison`,
`GET /dashboard/sentiment-trend?granularity=day|week|month`,
`GET /dashboard/rating-distribution`,
`GET /dashboard/frequent-terms?app_source_id=&label=&top_n=`.

## Ekspor

- `GET /datasets/{id}/splits/{split_id}/export/train` — CSV data training.
- `GET /datasets/{id}/splits/{split_id}/export/test` — CSV data testing.
- `GET /training-runs/{id}/export/predictions` — CSV hasil prediksi.
- `GET /training-runs/{id}/export/metrics` — CSV ringkasan metrik.
- `GET /training-runs/{id}/export/classification-report` — CSV per kelas.
- `GET /training-runs/{id}/export/confusion-matrix.png` — gambar PNG.
- `GET /training-runs/{id}/export/summary.pdf` — ringkasan lengkap PDF.

## Kode Error Umum

| HTTP Status | Kapan Terjadi |
|---|---|
| 400 | Validasi bisnis gagal (mis. split tidak feasible, model belum dilatih). |
| 401 | Token tidak ada/tidak valid/kedaluwarsa. |
| 403 | Akun tidak aktif. |
| 404 | Resource tidak ditemukan. |
| 409 | Konflik unique constraint (mis. package_id duplikat). |
| 413 | Ukuran file upload melebihi batas. |
| 415 | Tipe file tidak didukung. |
| 422 | Payload request tidak valid (validasi Pydantic). |
| 429 | Rate limit terlampaui. |
| 500 | Kesalahan tak terduga di server (dicatat ke log). |
