# TB-INSIGHT

Repository penelitian dan pengembangan produk untuk eksplorasi spatio-temporal tuberkulosis di Indonesia. Workspace dipisahkan menjadi dua produk agar data sintetis untuk demonstrasi tidak tercampur dengan analisis berbasis data nyata.

> **Penting:** seluruh angka dalam `product-demo-synthetic/` hanya untuk demonstrasi. Hanya artefak di `product-ongoing-real-data/` yang boleh digunakan untuk penelitian, setelah melewati pemeriksaan kualitas dan keterbatasan data.

## Struktur repository

```text
TB-INSIGHT/
├── product-demo-synthetic/       # Prototype UI/UX dengan data sintetis
├── product-ongoing-real-data/    # Riset nasional berbasis sumber resmi
├── .gitignore
└── README.md
```

## 1. Product Demo Synthetic

Folder: [`product-demo-synthetic/`](product-demo-synthetic/)

Prototype Surabaya untuk memperagakan pengalaman produk: peta risiko, profil kecamatan, forecasting, early warning, dan simulasi alokasi tenaga kesehatan. Seluruh angka epidemiologi, sosial, kapasitas, prediksi, dan rekomendasinya adalah **synthetic**.

Gunakan untuk:

- demo UI/UX dan alur pengguna;
- pengujian integrasi frontend–backend;
- diskusi fitur dengan stakeholder;
- eksperimen engineering tanpa menyentuh data produksi.

Jangan gunakan untuk publikasi, laporan epidemiologi, evaluasi program, atau keputusan kebijakan/anggaran.

## 2. Product Ongoing Real Data

Folder: [`product-ongoing-real-data/`](product-ongoing-real-data/)

Project penelitian nasional berbasis sumber resmi Kemenkes/SITB, BPS, NASA POWER, BIG, dan BNPB. Unit analisis utamanya adalah 38 provinsi × 24 bulan pada 2024–2025.

Gunakan untuk:

- penelitian spatio-temporal;
- analisis hubungan iklim dan kerentanan sosial;
- dashboard resmi berbasis data nyata;
- penyusunan paper dan dokumentasi metodologis.

## Aturan pemisahan

- Data atau output demo tidak boleh disalin ke product ongoing.
- Komponen UI dari demo boleh diadaptasi, tetapi harus dihubungkan ulang ke definisi variabel real.
- Model demo tidak dianggap baseline ilmiah untuk product ongoing.
- Setiap visual harus menampilkan status data: `SYNTHETIC DEMO` atau `OFFICIAL/REAL DATA`.
- Pekerjaan riset baru dilakukan di `product-ongoing-real-data`.

Brief rinci tersedia pada:

- [Brief product demo](product-demo-synthetic/PRODUCT_BRIEF.md)
- [Brief product ongoing](product-ongoing-real-data/PRODUCT_BRIEF.md)

## Mulai bekerja

Pilih jalur kerja sebelum menjalankan aplikasi atau pipeline:

- Penelitian dan pengolahan data: baca [`product-ongoing-real-data/README.md`](product-ongoing-real-data/README.md).
- Demo produk: baca [`product-demo-synthetic/README.md`](product-demo-synthetic/README.md).
- Sprint enam minggu: lihat dokumen dan workbook pada [`product-ongoing-real-data/deliverables/`](product-ongoing-real-data/deliverables/).
- Handoff M3 ke S4: gunakan [`outputs/2026-10-18-m3-to-s4-github/TB_INSIGHT_M3_to_S4_Direction.xlsx`](outputs/2026-10-18-m3-to-s4-github/TB_INSIGHT_M3_to_S4_Direction.xlsx). Seluruh input pada workbook menunjuk ke path kanonis dalam repository ini.

Untuk memvalidasi panel penelitian yang sudah tersedia:

```powershell
cd product-ongoing-real-data
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-analysis.txt
python scripts\validate_project.py
```

## Tata kelola data

- Outcome bulanan SITB merepresentasikan pasien yang memulai pengobatan, bukan estimasi insidensi TB.
- Data BPS digunakan sebagai kovariat tahunan atau reference-period; tidak direkonstruksi menjadi observasi bulanan tanpa dasar metodologis.
- Data 2025 harus diperlakukan sebagai provisional sampai pembaruan resmi tersedia.
- Setiap dataset harus memiliki sumber, periode, unit, tanggal akses, dan catatan transformasi.
- File sintetis dilarang masuk ke pipeline maupun output penelitian.

## Alur kontribusi

1. Buat branch dari `main` dengan pola `feature/<nama-singkat>` atau `analysis/<nama-singkat>`.
2. Simpan perubahan pada produk yang sesuai; jangan mencampur data demo dan data nyata.
3. Jalankan validator atau test yang relevan sebelum membuka pull request.
4. Cantumkan lokasi output, acceptance criteria, sumber data, dan keterbatasan pada pull request.
5. Perubahan hasil analisis harus ditinjau oleh anggota lain sebelum digabungkan ke `main`.

## Status penelitian

Fokus aktif adalah baseline reproducible untuk panel 38 provinsi × 24 bulan (2024–2025), eksplorasi spatio-temporal, climate anomaly, kerentanan sosial, spatial weights, PPML fixed effects, dan sensitivity analysis. Forecasting operasional belum menjadi keluaran utama karena panjang deret waktu masih terbatas.
