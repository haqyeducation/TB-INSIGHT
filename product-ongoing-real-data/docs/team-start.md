# Panduan mulai untuk tim

## Tujuan sprint pertama

Menghasilkan baseline spatio-temporal yang dapat direproduksi dari panel 38 provinsi × 24 bulan, tanpa menambah data synthetic dan tanpa memperluas klaim melebihi definisi outcome.

## Pembagian kerja yang disarankan

### 1. Data dan QA

- jalankan `python scripts/validate_project.py`;
- audit distribusi, outlier, dan missing tambahan;
- periksa `outcome_pending` serta kematangan kohort;
- dokumentasikan setiap perubahan di source ledger.

### 2. Analisis spasial

- siapkan matriks ketetanggaan provinsi yang dapat direproduksi;
- hitung Global Moran's I untuk count dan rate;
- buat LISA/hotspot dengan koreksi pengujian berganda;
- periksa sensitivitas provinsi kepulauan dan batas Papua.

### 3. Analisis temporal dan iklim

- mulai dari plot bulan, anomali, dan cross-correlation deskriptif;
- gunakan PPML dengan offset populasi, fixed effect provinsi, dan fixed effect periode;
- batasi lag utama pada 0–3 bulan;
- uji interaksi iklim dengan kemiskinan, kepadatan, atau sanitasi satu per satu.

### 4. Dashboard dan komunikasi

- tampilkan peta/rate, tren treatment initiation, anomali iklim, dan data maturity;
- sertakan definisi indikator serta sumber pada setiap halaman;
- jangan menampilkan prediksi atau skor risiko sebelum model dan validasinya disepakati.

## Definition of done

Sebuah pekerjaan dianggap selesai jika:

- dapat dijalankan ulang dari script atau notebook yang disimpan;
- input dan output mempunyai path yang jelas;
- angka utama direkonsiliasi dengan file QA;
- asumsi, limitation, dan definisi outcome tertulis;
- tidak ada file pribadi, cache, dependency lokal, atau data synthetic yang ikut dikomit.

## Urutan membaca

1. `README.md`
2. `docs/project-protocol.md`
3. `docs/data-audit.md`
4. `data/processed/analysis_panel_tb_climate_codebook.csv`
5. `data/processed/project_source_ledger.csv`

