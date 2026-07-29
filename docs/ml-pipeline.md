# Pipeline Machine Learning

## 1. Preprocessing (`app/services/preprocessing.py`)

Dijalankan berurutan untuk setiap ulasan (`POST /datasets/{id}/preprocess`,
berjalan di background, idempoten):

1. **Case folding** — mengubah teks menjadi huruf kecil.
2. **Cleaning** — menghapus URL, email, tag HTML, mention (`@user`), tanda
   pagar hashtag (isi kata dipertahankan), emoji, angka berdiri sendiri,
   tanda baca, karakter berulang berlebihan (`baguuuus` → `baguus`), dan
   whitespace berlebih.
3. **Normalisasi** — mengganti kata tidak baku menjadi kata baku berdasarkan
   tabel `normalization_dictionary` (dapat dikelola lewat menu Kamus).
4. **Tokenizing** — memecah teks menjadi token berbasis whitespace.
5. **Stopword removal** — membuang token yang ada di tabel `stopwords`,
   **kecuali** kata negasi (`tidak`, `bukan`, `belum`, `jangan`, `kurang`,
   `tanpa`, `nggak`) yang selalu dipertahankan apa pun isi tabel stopword.
6. **Stemming** — memakai Sastrawi (`StemmerFactory`), dengan daftar
   pengecualian (`STEMMING_EXCEPTIONS`) untuk nama aplikasi/istilah domain
   yang tidak boleh diubah bentuknya.
7. **Final text** — hasil akhir yang dipakai sebagai input TF-IDF & labelisasi
   kamus.

Setiap tahap disimpan di tabel `preprocessing_results` agar dapat ditampilkan
di aplikasi sebagai bukti proses (menu Detail Ulasan).

## 2. Labelisasi Kamus Sentimen (`app/services/labeling.py`)

```
positive_score = Σ (bobot kata positif × jumlah kemunculan di final_text)
negative_score = Σ (bobot kata negatif × jumlah kemunculan di final_text)
sentiment_score = positive_score - abs(negative_score)
```

Aturan label: `sentiment_score > 0` → **positive**, `< 0` → **negative**,
`= 0` → **neutral**. Pencocokan kata memakai *word boundary* pada string
`final_text` sehingga entri kamus berupa frasa (multi-kata) juga didukung.

- **Mode binary** (default): kelas `positive`/`negative` saja. Data `neutral`
  tetap dihitung/ditampilkan tapi ditandai `is_excluded_from_training=true`
  dan **tidak** ikut serta pada split/training/evaluation.
- **Mode ternary**: seluruh kelas (`positive`/`neutral`/`negative`) ikut
  serta pada split/training/evaluation.

## 3. Split Data (`app/services/splitting.py`)

Parameter: `train_size`, `test_size` (harus berjumlah 1.0), `random_state`
(default 42, untuk reproducibility), `stratify` (default aktif), `label_mode`.

Sebelum split, sistem memeriksa:
- Jumlah data minimal 2.
- Bila `stratify=true`: tiap kelas harus punya ≥2 anggota, dan ukuran data
  testing harus ≥ jumlah kelas. **Bila syarat tidak terpenuhi, split GAGAL
  dengan pesan yang menjelaskan kelas/alasan spesifik** — sistem **tidak**
  otomatis fallback ke non-stratified split.

ID review pada train/test set disimpan di `data_splits.train_review_ids` /
`test_review_ids` (JSON array) sehingga hasil split dapat direproduksi persis
kapan pun (dipakai ulang saat training, ekspor, maupun prediksi tetangga
terdekat).

## 4. TF-IDF (`app/services/tfidf_service.py`)

Memakai `sklearn.feature_extraction.text.TfidfVectorizer`. Parameter yang
dapat dikonfigurasi (dengan default): `max_features` (5000), `min_df` (2),
`max_df` (0.9), `ngram_range` (1,1), `sublinear_tf` (false), `norm` (`l2`).
Vectorizer **hanya di-fit pada data training** (bukan seluruh dataset),
kemudian dipakai untuk men-transform data testing — mencegah data leakage.

Disimpan: konfigurasi, jumlah vocabulary, daftar feature names, nilai IDF
per fitur, dan file model (`joblib`) di `tfidf_models`.

## 5. K-Nearest Neighbor (`app/services/knn_service.py`)

Memakai `sklearn.neighbors.KNeighborsClassifier`. Default: `n_neighbors=3`,
`metric=euclidean`, `algorithm=brute`, `weights=uniform`. Jarak dihitung
dengan **Euclidean Distance** sesuai metodologi penelitian.

### Training tunggal — `POST /datasets/{id}/train`

Melatih satu model dengan konfigurasi TF-IDF & K-NN yang ditentukan,
mengevaluasi pada data testing, menyimpan model (joblib), metrik, dan
prediksi per item testing (termasuk daftar tetangga terdekat).

### Eksperimen K — `POST /datasets/{id}/experiment-k`

Melatih beberapa nilai K (default `[1, 3, 5, 7, 9, 11]`, dapat dikustomisasi)
memakai TF-IDF yang sama (fit sekali), mencatat accuracy, precision, recall,
F1-score (weighted), waktu training, dan waktu prediksi untuk **setiap K**
sebagai baris `training_run_items`.

**Pemilihan model terbaik**: berdasarkan `selection_metric` (default
`f1_weighted`); jika seri, K yang lebih kecil dipilih (`is_selected=true`).
K yang lebih besar dari jumlah data training otomatis dilewati (dicatat di
`error_message`).

### Aktivasi Model

Training run pertama pada sebuah dataset **otomatis diaktifkan** (karena
belum ada yang digantikan). Training run berikutnya **tidak pernah**
menggantikan model aktif tanpa konfirmasi eksplisit lewat
`POST /training-runs/{id}/activate` dengan `{"confirm": true}`.

## 6. Evaluasi (`app/services/evaluation_service.py`)

Metrik dihitung dengan `zero_division=0` (tidak pernah crash walau suatu
kelas tidak pernah diprediksi), disertai daftar `warnings` bila hal itu
terjadi. Tersedia: `accuracy`, `precision`/`recall`/`f1` (macro & weighted),
`support` per kelas, `confusion_matrix`, dan `classification_report` lengkap.

## 7. Prediksi Satu Teks (`app/services/prediction_service.py`)

1. Teks input diproses lewat pipeline preprocessing yang sama (memakai kamus
   normalisasi & stopword **terkini**, bukan snapshot lama).
2. Di-transform dengan TF-IDF vectorizer dari training run yang dipilih
   (atau model aktif bila tidak ditentukan — lihat
   [docs/assumptions.md](assumptions.md)).
3. K-NN memprediksi label + `kneighbors()` mengembalikan K tetangga terdekat.
4. Tetangga terdekat dipetakan kembali ke teks & label ulasan training asli
   (direkonstruksi dari `data_splits.train_review_ids`, sehingga tidak perlu
   menyimpan salinan data training terpisah).
5. `confidence` dihitung sebagai proporsi tetangga yang labelnya sama dengan
   label prediksi (bukan probabilitas kalibrasi formal — K-NN tidak
   menghasilkan probabilitas asli).

Hasil prediksi (baik dari evaluasi batch maupun prediksi satu teks) disimpan
di tabel `predictions` dengan kolom `source` (`evaluation` atau `single`)
untuk membedakan konteksnya.
