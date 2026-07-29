# scripts/

Skrip operasional backend (`create_admin.py`, `seed_reference_data.py`) berada
di [`backend/scripts/`](../backend/scripts/) karena keduanya mengimpor modul
`app.*` milik backend secara langsung. Direktori level-monorepo ini
disediakan untuk skrip lintas-proyek di masa depan (mis. otomatisasi rilis
gabungan backend+mobile) dan sengaja dikosongkan untuk saat ini.
