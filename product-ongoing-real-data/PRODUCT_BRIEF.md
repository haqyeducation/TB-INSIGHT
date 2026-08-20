# Product brief — Ongoing Real Data

## Visi

Membangun TB-INSIGHT sebagai platform penelitian dan monitoring spatio-temporal yang transparan, reproducible, dan jujur terhadap keterbatasan data program TB Indonesia.

## Pertanyaan penelitian utama

1. Bagaimana pola spasial dan temporal pasien yang memulai pengobatan TBC sensitif obat di provinsi Indonesia selama 2024–2025?
2. Apakah anomali temperatur, kelembapan, dan curah hujan berasosiasi dengan perubahan treatment initiation?
3. Apakah asosiasi tersebut berbeda menurut kemiskinan, kepadatan penduduk, dan akses sanitasi?
4. Apakah terdapat hotspot/coldspot yang persisten setelah memperhitungkan populasi dan waktu?

## Data yang tersedia

- outcome SITB: 38 provinsi × 24 bulan;
- iklim NASA POWER dan normal 1991–2020;
- populasi, kepadatan, kemiskinan, dan sanitasi BPS;
- batas wilayah BIG untuk agregasi spasial;
- kejadian bencana BNPB sebagai sensitivity covariate.

Outcome utama adalah pasien mulai pengobatan, bukan insidensi TB. BPS merupakan konteks tahunan/reference-period, bukan observasi bulanan. Outcome pengobatan 2025 masih provisional.

## Produk yang akan dibangun

### Jalur penelitian

- dataset dan QA yang dapat direproduksi;
- exploratory spatio-temporal analysis;
- Moran's I, LISA, dan peta hotspot;
- PPML fixed effects dengan offset populasi;
- heterogenitas iklim × kerentanan sosial;
- sensitivity analysis spasial dan kematangan kohort;
- manuskrip ilmiah dan supplementary materials.

### Jalur aplikasi

- dashboard provenance-first;
- tren treatment initiation dan data maturity;
- peta count, rate, anomali iklim, dan hotspot;
- halaman metode, sumber, dan keterbatasan;
- tanpa forecasting operasional sampai panjang seri memadai.

## Roadmap kerja

### Fase 1 — Baseline reproducible

- bekukan versi panel dan checksum;
- selesaikan data dictionary dan QA notebook;
- buat EDA nasional dan profil setiap provinsi;
- tetapkan satu outcome primer dan satu spesifikasi model primer.

### Fase 2 — Spatial foundation

- buat adjacency matrix yang terversi;
- uji Global Moran's I dan LISA;
- periksa sensitivitas provinsi kepulauan serta wilayah Papua;
- uji autokorelasi residual model utama.

### Fase 3 — Climate and social vulnerability

- gunakan anomali/z-score iklim, bukan musim nasional tunggal;
- batasi lag utama 0–3 bulan;
- uji interaksi sosial satu per satu untuk menghindari overfitting;
- dokumentasikan multiple testing dan uncertainty.

### Fase 4 — Dashboard dan manuskrip

- sinkronkan visual dengan output analisis tervalidasi;
- tampilkan definisi dan provenance pada setiap halaman;
- tulis Methods, Results, limitation, dan reproducibility appendix;
- siapkan repository release tanpa raw data yang lisensinya membatasi redistribusi.

### Fase 5 — Penguatan data

- ajukan data SITB historis 2021–2025 melalui Kemenkes;
- harmonisasi perubahan 34 menjadi 38 provinsi jika data lama diperoleh;
- lakukan preregistration/update analysis plan sebelum memperluas model.

## Pembagian tim

- Data/QA: ekstraksi, validasi, provenance, dan versioning.
- Spatial: boundary, weights, Moran/LISA, dan peta.
- Modeling: PPML, lag, interaction, dan sensitivity analysis.
- Product: API, dashboard, UX, dan data-status messaging.
- Research writing: literatur, metode, interpretasi, dan manuskrip.

## Definition of done

- semua angka dapat ditelusuri ke file dan sumber;
- script berjalan ulang dari README;
- unit, periode, dan definisi outcome konsisten;
- hasil membedakan fakta, interpretasi, dan hipotesis;
- limitation ditampilkan bersama hasil;
- tidak ada data atau output synthetic di product ini.

