# Keputusan skala data TB-INSIGHT

Tanggal keputusan: 20 Agustus 2026

## Keputusan

Analisis utama menggunakan panel nasional tingkat **provinsi-bulan**, Januari 2024–Desember 2025:

- 38 provinsi;
- 24 bulan;
- 912 observasi unik;
- outcome utama: pasien yang mulai pengobatan TBC sensitif obat;
- eksposur utama: anomali temperatur, kelembapan, dan curah hujan;
- konteks sosial: populasi, kepadatan, kemiskinan, dan sanitasi BPS;
- bencana BNPB hanya sebagai kovariat sensitivitas.

Panel Surabaya dan seluruh data synthetic tidak termasuk project produksi.

## Mengapa skala ini dipilih

SITB menyediakan ekspor publik yang konsisten untuk 38 provinsi × 12 bulan pada 2024 dan 2025. Endpoint historis dengan struktur dan definisi yang sama untuk 2019–2023 tidak tersedia secara publik. Seri SATUSEHAT yang lebih panjang hanya valid pada tingkat nasional, sedangkan sumber provinsi sebelum 2024 yang ditemukan umumnya tahunan atau hanya mencakup sebagian wilayah.

Panel 912 observasi cukup untuk:

- pemetaan beban dan rate;
- Global Moran's I dan LISA per periode yang dipilih;
- model count dengan fixed effect provinsi dan waktu;
- analisis heterogenitas menurut kerentanan sosial;
- sensitivity analysis menggunakan bencana dan definisi kohort matang.

Panel ini belum cukup untuk:

- forecasting jangka panjang;
- klaim kausal;
- distributed lag non-linear model yang sangat fleksibel;
- menyimpulkan pola musim nasional hanya dari dua siklus tahunan;
- menyebut jumlah pasien mulai pengobatan sebagai insidensi TB.

## Produk data yang digunakan

- `data/processed/analysis_panel_tb_climate_disaster_2024_2025.csv`
- `data/processed/analysis_panel_tb_climate_codebook.csv`
- `data/processed/project_source_ledger.csv`
- `data/processed/analysis_panel_tb_climate_validation.json`
- `data/processed/tb_treatment_outcomes_province_month_official.csv`

## Aturan interpretasi

1. Gunakan istilah *treatment initiation* atau pasien mulai pengobatan.
2. BPS tetap merupakan kovariat tahunan/reference-period meskipun digabungkan ke setiap bulan.
3. Outcome pengobatan 2025 masih provisional; gunakan `outcome_pending` dan definisi kohort matang.
4. BNPB merupakan analisis sensitivitas karena tabel operasional tidak sepenuhnya sama dengan workbook tahunan.
5. Hubungan iklim dibaca sebagai asosiasi ekologis, bukan efek individual atau kausal.

## Jalur peningkatan data

Jika Kementerian Kesehatan memberikan data agregat historis, prioritasnya adalah provinsi-bulan 2021–2025 dengan definisi indikator konsisten. Periode sebelum pemekaran Papua harus memakai harmonisasi batas 34 provinsi atau rekonstruksi resmi ke 38 provinsi. Sampai data tersebut tersedia, panel 2024–2025 tetap menjadi basis resmi project.
