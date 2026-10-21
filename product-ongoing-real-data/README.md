# TB-INSIGHT — Product Ongoing Real Data

TB-INSIGHT adalah project riset ekologi **spatio-temporal** untuk menganalisis pola pasien yang memulai pengobatan TBC sensitif obat di 38 provinsi Indonesia, Januari 2024–Desember 2025. Project ini hanya memakai data nyata yang dapat ditelusuri ke Kementerian Kesehatan/SITB, BPS, NASA POWER, BIG, dan BNPB.

> Outcome utama adalah `treatment_started` / pasien mulai pengobatan, bukan estimasi insidensi TB dan bukan seluruh notifikasi kasus.

## Mulai dari sini

1. Baca [protokol project](docs/project-protocol.md).
2. Baca [audit data TB bulanan](docs/data-audit.md).
3. Baca [panduan mulai untuk tim](docs/team-start.md).
4. Gunakan [panel analisis final](data/processed/analysis_panel_tb_climate_disaster_2024_2025.csv).
5. Periksa [codebook](data/processed/analysis_panel_tb_climate_codebook.csv) sebelum memakai variabel.
6. Periksa [source ledger](data/processed/project_source_ledger.csv) sebelum menulis klaim atau sitasi data.
7. Untuk hasil koreksi Sprint 3, baca [S3 canonical rebuild](docs/S3_REBUILD_REPORT.md).
8. Untuk melanjutkan ke Sprint 4, gunakan [workbook arahan M3 ke S4](../outputs/2026-10-18-m3-to-s4-github/TB_INSIGHT_M3_to_S4_Direction.xlsx). Path input di dalamnya relatif terhadap root repository.

## Struktur folder

```text
TB-INSIGHT/
├── backend/        API FastAPI untuk dashboard
├── frontend/       aplikasi React/Vite, tanpa build dan dependency lokal
├── data/
│   ├── raw/        snapshot sumber resmi; jangan diedit
│   └── processed/  hasil kurasi, validasi, codebook, dan panel analisis
├── deliverables/   workbook siap dibaca/dibagikan
├── docs/           keputusan data, audit, desain, dan protokol riset
├── results/        hasil model eksploratif
└── scripts/        pipeline reproduksi dan validasi
```

## Dataset utama

| Komponen | Cakupan | Peran |
|---|---|---|
| SITB kohort pengobatan | 38 provinsi × 24 bulan | Outcome utama |
| NASA POWER | 38 provinsi × 24 bulan + normal 1991–2020 | Temperatur, kelembapan, hujan, dan anomali |
| BPS | Tahunan/reference-period | Populasi, kepadatan, kemiskinan, sanitasi |
| BNPB | 38 provinsi × 24 bulan | Kovariat sensitivitas bencana |
| BIG | Batas provinsi | Agregasi spasial iklim |

Panel final memiliki **912 baris, 38 provinsi, 24 bulan, tanpa duplikasi kunci dan tanpa missing pada variabel wajib**. Outcome 2025 masih provisional; `outcome_pending` wajib diperhatikan ketika menganalisis keberhasilan pengobatan.

## Menjalankan pipeline data

Gunakan Python 3.11 atau lebih baru.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-analysis.txt
python scripts\run_pipeline.py
python scripts\validate_project.py
```

Pipeline memakai snapshot yang sudah ada pada `data/raw`. Ekstraksi ulang SATUSEHAT bersifat opsional dan memerlukan Playwright serta akses internet.

## Menjalankan aplikasi

Backend:

```powershell
pip install -r backend\requirements.txt
python backend\main.py
```

Frontend pada terminal kedua:

```powershell
cd frontend
pnpm install --frozen-lockfile=false
pnpm run dev

npm ci
npm run dev
```

API berjalan di `http://localhost:8000`, sedangkan Vite menampilkan alamat frontend pada terminal. Untuk deployment, project juga menyediakan `Dockerfile`.

## Aturan kolaborasi

- Jangan mengedit file pada `data/raw`.
- Jangan menambahkan data dummy atau synthetic ke pipeline produksi.
- Setiap dataset baru harus memiliki URL penerbit, tanggal akses, definisi indikator, unit, cakupan, dan catatan keterbatasan.
- Jangan menyebut outcome utama sebagai insidensi TB.
- Perubahan data harus diikuti pembaruan file validasi dan `project_source_ledger.csv`.
- Hasil model dua tahun diperlakukan sebagai asosiasi eksploratif, bukan klaim kausal atau forecasting jangka panjang.

## Deliverable yang tersedia

- [Workbook panel TB–iklim](deliverables/tb_climate_project_analysis_ready.xlsx)
- [Workbook TB nasional dan provinsi](deliverables/tb_national_province_analysis_ready.xlsx)
- [Hasil PPML awal](results/preliminary_tb_climate_ppml_results.csv)
- [Model lag iklim 0–3](results/models/climate_lags/coefficients_all_lags.csv)
- [Model interaksi iklim × sosial](results/models/social_interactions/coefficients_all_interactions.csv)
- [Hasil LISA bulanan](results/spatial/hotspot_monthly_lisa.csv)
- [Boundary dan weights kanonis](data/processed/spatial/)
