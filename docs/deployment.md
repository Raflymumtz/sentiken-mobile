# Panduan Deployment

## Development (Docker Compose)

Cara tercepat dan direkomendasikan — lihat [README.md](../README.md#menjalankan-dengan-docker).

```bash
cp .env.example .env   # sesuaikan nilainya
docker compose up --build
```

## Deployment ke Server (Produksi Kecil/Menengah)

Proyek ini dirancang untuk skala penelitian/single-team, bukan untuk traffic
publik masif. Untuk deployment di VPS/server:

1. **Environment variable**: jangan pernah commit `.env` asli. Gunakan secret
   manager platform (mis. Docker secrets, systemd EnvironmentFile, atau
   secret manager cloud) untuk `JWT_SECRET_KEY`, `ADMIN_PASSWORD`,
   `POSTGRES_PASSWORD`.
2. **CORS**: set `CORS_ALLOWED_ORIGINS` ke origin spesifik (bukan `*`) dan
   `ENVIRONMENT=production`.
3. **Database**: gunakan PostgreSQL terkelola (backup otomatis) atau volume
   Docker dengan backup rutin (`pg_dump`).
4. **Redis + worker**: set `JOB_EXECUTION_MODE=rq` dan jalankan container
   `worker` terpisah (dapat diskalakan menjadi beberapa replica bila beban
   scraping/training tinggi).
5. **Reverse proxy**: taruh Nginx/Caddy/Traefik di depan `backend` (port
   8000) untuk TLS termination dan rate limiting tambahan di edge.
6. **Storage model**: volume `model_storage` (`/app/storage`) harus persisten
   antar deployment — model joblib & hasil ekspor disimpan di sana.
7. **Migration**: jalankan `alembic upgrade head` sebagai langkah deployment
   terpisah (bukan otomatis di setiap restart container produksi) agar migrasi
   terkontrol; command default di `docker-compose.yml` cocok untuk
   development tapi pertimbangkan pipeline CI/CD terpisah untuk produksi.
8. **Mobile (Expo)**: build produksi dengan **EAS Build**
   (`npx eas build --platform android|ios`), arahkan `EXPO_PUBLIC_API_URL`
   ke domain publik backend (HTTPS).

## Checklist Sebelum Produksi

- [ ] `JWT_SECRET_KEY` unik & acak (≥32 karakter).
- [ ] `ADMIN_PASSWORD` diganti dari nilai contoh.
- [ ] `POSTGRES_PASSWORD` diganti dari nilai contoh.
- [ ] `CORS_ALLOWED_ORIGINS` tidak `*`.
- [ ] `ENVIRONMENT=production`.
- [ ] Backup database terjadwal aktif.
- [ ] Volume `model_storage` persisten & dicadangkan.
- [ ] HTTPS aktif di depan backend (reverse proxy/load balancer).
- [ ] Rate limit (`RATE_LIMIT_PER_MINUTE`) disesuaikan dengan kapasitas server.
