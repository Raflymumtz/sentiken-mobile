# scripts/

Skrip operasional backend (`create_admin.py`, `seed_reference_data.py`) berada
di [`backend/scripts/`](../backend/scripts/) karena keduanya mengimpor modul
`app.*` milik backend secara langsung. Direktori level-monorepo ini berisi
skrip lintas-proyek.

## Menjalankan backend di laptop pribadi dengan akses jarak jauh

Untuk skenario dev/personal: backend jalan di laptop, diekspos ke internet
lewat Cloudflare Tunnel (URL berubah tiap restart), dan aplikasi mobile
otomatis mengambil URL terbaru dari `mobile/remote-config.json` di GitHub
(lihat `mobile/lib/api/remoteConfig.ts`) -- jadi APK tidak perlu dibangun
ulang setiap kali URL tunnel berubah.

- `start-local-server.ps1` -- menyalakan backend (uvicorn) + Cloudflare
  Tunnel bila belum jalan, lalu meng-update & push `mobile/remote-config.json`
  dengan URL tunnel terbaru.
- `register-startup-task.ps1` -- jalankan **sekali** secara manual untuk
  mendaftarkan `start-local-server.ps1` di Task Scheduler Windows (trigger
  "At log on"), supaya semuanya otomatis tiap kali laptop di-restart/login,
  tanpa perlu perintah manual lagi.

Prasyarat: `cloudflared` terpasang, `backend/.venv` sudah lengkap, dan
`git push` ke repo ini sudah bisa jalan tanpa prompt (kredensial GitHub
tersimpan).
