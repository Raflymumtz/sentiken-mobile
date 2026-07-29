# Asumsi & Keputusan Teknis

Dokumen ini mencatat keputusan teknis yang diambil ketika spesifikasi tidak
menjelaskan detail implementasi secara eksplisit. **Tidak ada asumsi yang
dibuat terhadap isi/hasil data penelitian** (tidak ada data ulasan atau
metrik yang direkayasa) — seluruh asumsi di bawah ini bersifat rekayasa
perangkat lunak (arsitektur, format, alur kerja).

## Autentikasi & Keamanan

- **Validasi email longgar, bukan `pydantic.EmailStr`.** `EmailStr` menolak
  TLD reserved seperti `.local`/`.internal` yang lazim dipakai untuk akun
  admin tunggal pada deployment lokal/riset. Backend memakai regex sederhana
  `x@y.z` pada `LoginRequest`.
- **Hashing password memakai `bcrypt` langsung**, bukan `passlib`, karena
  `passlib` (tidak lagi dikelola aktif) memiliki bug kompatibilitas dengan
  `bcrypt>=4.1` yang menyebabkan error saat deteksi versi backend.
- **Refresh token revocation** disimpan in-memory (set JTI yang di-revoke).
  Cukup untuk skala single-instance penelitian ini; untuk multi-instance
  produksi, ganti dengan Redis set.
- **Rate limiting** adalah sliding-window in-memory per IP pada satu proses
  backend. Untuk deployment multi-instance, ganti dengan backend Redis.

## Background Job

- **Dua mode eksekusi job**: `inline` (thread pool lokal, default
  development/testing, tanpa Redis) dan `rq` (Redis + container `worker`,
  direkomendasikan untuk beban lebih berat). Bila mode `rq` dipilih namun
  Redis tidak dapat dihubungi, job otomatis fallback ke eksekusi inline
  (dicatat sebagai warning di log) — sesuai instruksi "implementasi
  background worker yang sederhana dan stabil" pada spesifikasi.
- **Test suite backend memakai SQLite berbasis file** (bukan `:memory:`)
  karena beberapa alur (collection job, import job, training) berjalan pada
  thread terpisah; satu koneksi SQLite mentah tidak aman dipakai bersamaan
  oleh >1 thread walau `check_same_thread=False`. SQLite berbasis file
  dengan busy-timeout aman untuk kasus ini.

## Data & Deduplikasi

- Review **wajib terhubung ke `dataset_id`** (bukan hanya `app_source_id`),
  karena workflow aplikasi mengelompokkan ulasan per dataset (hasil satu
  proses pengumpulan/import). Setiap dataset terhubung ke satu `app_source`.
- **Fingerprint dedup** dihitung dari `app_source_id + content + username +
  review_date` (SHA-256) dan dipakai ketika `review_id` kosong (mis. sebagian
  baris CSV). Saat `review_id` tersedia, pengecekan duplikat memakai
  `(app_source_id, review_id)` — sesuai constraint unik pada tabel `reviews`.

## Preprocessing

- **Daftar stemming exception** (nama aplikasi/istilah domain yang tidak
  di-stem) disimpan sebagai konstanta di kode
  (`app/services/preprocessing.py: STEMMING_EXCEPTIONS`), bukan tabel
  database terpisah, karena spesifikasi tidak mencantumkan tabel khusus
  untuk ini di antara 20 tabel wajib. Dapat diperluas langsung di kode.
- **Kamus starter** (`app/data/seed_dictionary.py`) berisi daftar kata
  positif/negatif/normalisasi Indonesia yang wajar untuk memulai, **bukan**
  leksikon penelitian yang sudah divalidasi/dipublikasikan. Pengguna
  diharapkan meninjau/menambah/menghapus/mengganti kata-kata ini lewat menu
  Kamus (termasuk import/export CSV) sebelum menjadikan hasil labelisasi
  sebagai temuan penelitian akhir.
- **Stopword seed** diambil dari daftar bawaan pustaka Sastrawi
  (`StopWordRemoverFactory`), dikurangi kata negasi (tidak, bukan, belum,
  jangan, kurang, tanpa, nggak) agar tidak terhapus saat stopword removal.

## Labelisasi

- **Rumus skor** mengikuti metodologi penelitian persis:
  `positive_score` = total bobot kata positif yang ditemukan (dihitung per
  kemunculan, bukan hanya kehadiran/presence), `negative_score` = total bobot
  kata negatif, `sentiment_score = positive_score - abs(negative_score)`.
  Pencocokan kata memakai word-boundary pada `final_text` hasil preprocessing
  (setelah stemming), sehingga entri kamus multi-kata (frasa) tetap dapat
  cocok sebagai substring berbatas kata.

## Split, TF-IDF, K-NN

- **Stratified split yang tidak memenuhi syarat akan GAGAL secara eksplisit**
  (bukan fallback otomatis ke non-stratified), sesuai instruksi "jangan
  menjalankan stratified split jika syaratnya tidak terpenuhi; tampilkan
  alasan kegagalan secara jelas".
- **Eksperimen-K tidak menyimpan model K-NN terpisah untuk setiap nilai K**
  yang diuji (hanya metrik + waktu training/prediksi per K, sesuai field
  yang diminta spesifikasi). TF-IDF vectorizer yang dipakai bersama pada
  eksperimen tetap disimpan. Untuk benar-benar mengaktifkan K terbaik hasil
  eksperimen, jalankan `POST /datasets/{id}/train` dengan `n_neighbors`
  sesuai rekomendasi (`is_selected=true` pada item eksperimen), lalu
  konfirmasi aktivasi lewat `POST /training-runs/{id}/activate`.
- **Aktivasi model otomatis HANYA terjadi jika dataset belum punya model
  aktif sama sekali** (training run pertama). Training run berikutnya tidak
  pernah menimpa model aktif tanpa konfirmasi eksplisit
  (`POST /training-runs/{id}/activate` dengan `confirm=true`) — sesuai
  instruksi "jangan mengganti model aktif tanpa konfirmasi pengguna".

## Prediksi Satu Teks

- Endpoint `POST /predictions/single` tidak menerima parameter `dataset_id`
  (sesuai daftar endpoint pada spesifikasi). Bila `training_run_id` tidak
  disertakan, backend memakai training run **yang paling terakhir
  diaktifkan secara global** (lintas dataset) sebagai model aktif implisit —
  cocok untuk konteks aplikasi mobile single-user yang berfokus pada satu
  model aktif dalam satu waktu (lihat bagian Dashboard pada spesifikasi yang
  menyebut "model aktif" secara tunggal).

## Ekspor

- Spesifikasi hanya mencantumkan `GET /datasets/{id}/export` secara eksplisit
  di daftar API, namun UI (bagian "Q. Ekspor") meminta banyak format
  (train/test data, predictions, metrics, classification report, confusion
  matrix PNG, summary PDF). Backend menambahkan endpoint pelengkap:
  - `GET /datasets/{id}/splits/{split_id}/export/train` & `/test`
  - `GET /training-runs/{id}/export/predictions|metrics|classification-report`
  - `GET /training-runs/{id}/export/confusion-matrix.png`
  - `GET /training-runs/{id}/export/summary.pdf`
- **Confusion matrix PNG** digambar manual dengan Pillow (dependensi yang
  sudah dibawa oleh `reportlab`), tanpa menambah dependensi chart baru.

## Dashboard & Perbandingan

- Statistik dashboard/perbandingan dihitung murni dari data yang ada di
  database (tidak pernah ada angka yang dikarang). Saat dataset belum punya
  data, endpoint mengembalikan `has_data: false` dan nilai nol/`null` —
  bukan data contoh yang terlihat seperti hasil sungguhan.
- **Frequent terms** dihitung dari `final_text` hasil preprocessing yang
  benar-benar ada di database (term frequency sederhana), tanpa inferensi
  penyebab keluhan apa pun di luar kata/frasa yang ditemukan — sesuai
  instruksi "jangan menyimpulkan penyebab keluhan tanpa dasar data".

## Lain-lain

- **Package ID seed** untuk PLN Mobile & MyPertamina memakai placeholder
  (`belum.diisi.<nama>`) bila environment variable terkait
  (`PLN_MOBILE_PACKAGE_ID`/`MYPERTAMINA_PACKAGE_ID`) kosong, dengan
  `is_active=false` sampai pengguna mengisi package ID sesungguhnya lewat
  aplikasi mobile atau environment variable — sesuai instruksi "jangan
  hard-code package ID yang belum diverifikasi".
- Sandbox pengembangan yang dipakai untuk membangun proyek ini **tidak
  memiliki Docker maupun Node.js**, sehingga `docker compose up` dan
  `npm install`/Expo tidak dapat dieksekusi langsung di lingkungan tersebut.
  Backend diverifikasi menyeluruh via `pytest` (SQLite) dan `alembic upgrade
  head` (SQLite); struktur Docker Compose divalidasi secara sintaksis
  (parsing YAML) tetapi belum dijalankan end-to-end pada Docker sungguhan.
  Mobile app diverifikasi lewat pemeriksaan kode/TypeScript secara manual,
  belum dijalankan di Expo Go/emulator. Lihat
  [docs/progress.md](progress.md) untuk detail status verifikasi per tahap.
