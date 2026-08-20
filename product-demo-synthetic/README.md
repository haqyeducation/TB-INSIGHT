# TB-INSIGHT — Product Demo Synthetic

Prototype tingkat kecamatan Surabaya untuk mendemonstrasikan fitur produk. **Semua nilai pada folder ini synthetic dan tidak mewakili kondisi TB sebenarnya.**

## Fitur demo

- tren TB bulanan simulasi;
- peta dan klaster risiko kecamatan;
- prediksi Januari–Maret 2026 berbasis data simulasi;
- early-warning prototype;
- simulasi alokasi tenaga kesehatan dan anggaran.

## Struktur

```text
product-demo-synthetic/
├── backend/       API FastAPI demo
├── frontend/      dashboard React/Vite demo
├── data/
│   ├── synthetic/ sumber dummy
│   ├── boundaries/ batas kecamatan
│   └── processed/ hasil pipeline demo
├── results/       grafik, peta, dan laporan hasil demo
├── scripts/       pipeline demo
└── docs/          dokumentasi konsep lama
```

## Menjalankan demo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python backend\main.py
```

Terminal kedua:

```powershell
cd frontend
npm ci
npm run dev
```

Pipeline synthetic dapat dibangun ulang dengan:

```powershell
python scripts\run_pipeline.py
```

## Larangan penggunaan

- Jangan menyebut nilai sebagai data Dinkes, BPS, atau keadaan Surabaya sebenarnya.
- Jangan memakai forecast, hotspot, atau alokasi sebagai rekomendasi operasional.
- Jangan menggabungkan file synthetic dengan panel pada product ongoing.
- Screenshot demo harus tetap memperlihatkan banner `DEMO SYNTHETIC`.

