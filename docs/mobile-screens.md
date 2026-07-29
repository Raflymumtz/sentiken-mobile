# Peta Layar Mobile

Aplikasi memakai **Expo Router** (file-based routing) dengan bottom navigation
5 tab. Semua layar berbahasa Indonesia, mendukung light/dark mode
(`lib/theme.ts` + `lib/hooks/useThemeColors.ts`), dan menampilkan
loading/empty/error state eksplisit alih-alih data palsu.

```
app/
├── index.tsx                         Redirect awal (loading singkat)
├── (auth)/
│   └── login.tsx                     A. Login (email, password, JWT)
└── (tabs)/
    ├── dashboard/
    │   └── index.tsx                 B. Dashboard (stat, model aktif, grafik)
    ├── dataset/
    │   ├── index.tsx                 F. Daftar Dataset
    │   ├── create.tsx                F. Buat Dataset (modal)
    │   └── [id]/
    │       ├── index.tsx             F. Detail Dataset + aksi
    │       ├── reviews.tsx           F/G. Daftar Ulasan + filter
    │       ├── import.tsx            E. Import CSV (preview → execute)
    │       └── review/[reviewId].tsx G. Detail Ulasan (preprocessing, label, tetangga)
    ├── proses/
    │   ├── index.tsx                 Pilih dataset + daftar tahapan pipeline
    │   └── [datasetId]/
    │       ├── collection.tsx        D. Pengumpulan Data (job scraping)
    │       ├── preprocess.tsx        I. Jalankan Preprocessing
    │       ├── label.tsx             J. Labelisasi Kamus Sentimen (binary/ternary)
    │       ├── split.tsx             K. Split Data Training/Testing
    │       ├── train.tsx             L/M. Latih Model TF-IDF + K-NN
    │       └── experiment.tsx        M. Eksperimen Nilai K
    ├── analisis/
    │   ├── index.tsx                 Menu analisis + daftar model per dataset
    │   ├── evaluasi/[runId].tsx      N. Hasil Evaluasi (confusion matrix, metrik, ekspor)
    │   ├── prediksi.tsx              O. Prediksi Satu Teks + tetangga terdekat
    │   └── perbandingan.tsx          P. Perbandingan Aplikasi (chart, term frekuensi)
    └── pengaturan/
        ├── index.tsx                 Menu pengaturan
        ├── sumber-aplikasi/index.tsx C. CRUD Sumber Aplikasi
        ├── kamus/[type].tsx          H. Kamus (positive/negative/normalization/stopwords)
        └── akun.tsx                  Profil, tema, logout
```

## Komponen Bersama (`components/ui/`)

`ScreenContainer`, `Card`, `StatCard`, `Badge`, `EmptyState`, `LoadingState`,
`ErrorState`, `PrimaryButton`, `TextField`, `ProgressBar`, `ConfirmDialog`,
`ToastHost` — dipakai konsisten di seluruh layar agar loading/empty
state/error state/konfirmasi/notifikasi seragam, sesuai kebutuhan UI/UX pada
spesifikasi (kartu statistik, skeleton/loading, pull-to-refresh, empty state,
retry state, confirmation dialog, toast, ukuran tombol ramah sentuhan ≥48dp,
label aksesibilitas).

## State Management

- **TanStack Query** (`lib/hooks/*.ts`) — seluruh data dari backend (server
  state), termasuk polling otomatis untuk job yang masih berjalan
  (`refetchInterval` menyesuaikan status).
- **Zustand** — hanya untuk state klien murni: sesi auth (`authStore`,
  disinkronkan ke `expo-secure-store`), preferensi tema (`settingsStore`),
  dan toast (`toastStore`).
- **React Hook Form + Zod** — seluruh form (login, buat dataset, pengumpulan
  data, split, kamus) divalidasi di sisi klien sebelum dikirim ke API.

## Autentikasi & Navigasi

`app/_layout.tsx` melakukan hidrasi token dari SecureStore saat aplikasi
dibuka, lalu mengarahkan ke `(auth)/login` bila belum ada token, atau ke
`(tabs)/dashboard` bila sudah login. Axios client (`lib/api/client.ts`)
otomatis menyisipkan Bearer token dan mencoba refresh token sekali saat
menerima 401 sebelum akhirnya logout paksa jika refresh turut gagal.

## Keterbatasan Verifikasi

Lingkungan pengembangan yang dipakai untuk membangun proyek ini **tidak
memiliki Node.js/npm**, sehingga `npm install`, `expo start`, dan `npm test`
belum bisa dijalankan langsung di lingkungan tersebut. Kode ditulis mengikuti
konvensi Expo Router v4 + TypeScript strict yang sudah mapan, dan struktur
import/path telah ditinjau ulang secara manual (termasuk pemeriksaan silang
setiap `router.push(...)` terhadap struktur file aktual). Sebelum dianggap
final, jalankan `npm install && npx expo install --fix && npm run typecheck
&& npm run lint && npm test` untuk verifikasi menyeluruh di lingkungan dengan
Node.js.
