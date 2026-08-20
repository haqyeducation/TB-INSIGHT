# Audit sumber TB provinsi-bulanan

Tanggal audit dan snapshot: 12 Agustus 2026 (Asia/Jakarta)

## Kesimpulan

Sumber publik yang memenuhi kebutuhan panel seluruh provinsi per bulan adalah TB Dashboard SITB Kementerian Kesehatan untuk kohort pasien yang mulai pengobatan TBC sensitif obat pada 2024 dan 2025:

- 38 provinsi x 12 bulan x 2 tahun = 912 baris provinsi-bulan;
- delapan indikator: jumlah pasien mulai pengobatan, sembuh, pengobatan lengkap, lost to follow up, meninggal, gagal, tidak dievaluasi/pindah, dan belum ada hasil;
- setiap kombinasi provinsi-bulan unik;
- tidak ada nilai negatif;
- tujuh kategori outcome menjumlah tepat ke jumlah pasien pada seluruh 912 baris;
- data merupakan snapshot dashboard hidup dan dapat direvisi.

Sumber resmi:

- https://tbdashboard.sitb.id/ss_data_tbc03so_2024_provinsi_bulanan_list.php
- https://tbdashboard.sitb.id/ss_data_tbc03so_2025_provinsi_bulanan_list.php

Dataset ini tidak boleh dilabeli sebagai insidensi atau seluruh notifikasi kasus. `jumlah_pasien` berarti pasien dalam kohort yang mulai pengobatan pada bulan tersebut.

## Audit rentang tahun

Lima pola URL tabel/ekspor diuji untuk setiap tahun 2019-2026. Hanya endpoint kohort 2024 dan 2025 yang mengembalikan HTTP 200; kandidat 2019-2023 dan 2026 mengembalikan 404. Pencarian indeks web dan Wayback Machine juga tidak menemukan arsip tabel provinsi-bulanan lama. Dengan demikian, data publik ini belum dapat diperpanjang menjadi panel 2021-2025 hanya melalui crawling.

Untuk memperoleh lima tahun historis, rute yang dapat dipertanggungjawabkan adalah permintaan agregat resmi kepada Kementerian Kesehatan/Pengelola SITB. Untuk lima tahun mendatang, crawler hanya dapat mengarsipkan rilis baru secara prospektif saat Kemenkes menerbitkannya; crawler tidak dapat memperoleh data yang belum ada.

## Penilaian kredibilitas

| Aspek | Penilaian | Dasar |
|---|---|---|
| Otoritas sistem | Tinggi | Portal `sitb.kemkes.go.id` menyatakan SITB sebagai Sistem Informasi Tuberkulosis Kementerian Kesehatan dan FAQ Kemenkes menunjuk `sitb.id` sebagai sistem input data asli |
| Keterlacakan ekspor | Tinggi | File diekspor langsung dari subdomain TB Dashboard SITB, disimpan tanpa perubahan, dan diberi SHA-256 |
| Kelengkapan struktur | Tinggi | 38 provinsi pada setiap bulan, tanpa duplikasi/negatif, dan seluruh outcome merekonsiliasi total pasien |
| Finalitas 2024 | Cukup tinggi | Kohort lebih matang, tetapi dashboard hidup tetap dapat direvisi |
| Finalitas 2025 | Sedang/provisional | Masih terdapat 112.593 outcome `belum_ada_hasil`; perbandingan keberhasilan belum final |
| Kesetaraan dengan insidensi/notifikasi | Tidak berlaku | Dataset adalah kohort mulai pengobatan TBC SO; bukan ukuran insidensi dan bukan seluruh notifikasi |
| Kovariat BPS | Tinggi untuk definisi/periode aslinya | Bersumber dari publikasi resmi BPS; bersifat tahunan/reference-period dan tidak diinterpolasi menjadi observasi bulanan |

Kesimpulan kredibilitas: dataset inti layak dan dapat dipertanggungjawabkan untuk analisis sesuai definisinya. Kredibel tidak berarti final, bebas under-reporting, atau dapat digunakan untuk klaim epidemiologi di luar variabel yang diterbitkan.

## Hasil ekstraksi

| Produk | Baris | Kegunaan |
|---|---:|---|
| `data/raw/sitb_dashboard/tb_treatment_outcomes_province_month_2024_raw.csv` | 456 | Ekspor mentah resmi 2024 |
| `data/raw/sitb_dashboard/tb_treatment_outcomes_province_month_2025_raw.csv` | 456 | Ekspor mentah resmi 2025 |
| `data/processed/tb_treatment_outcomes_province_month_official.csv` | 912 | Format lebar, satu baris per provinsi-bulan |
| `data/processed/tb_province_month_sitb_official.csv` | 7.296 | Format panjang, satu baris per provinsi-bulan-indikator |
| `data/processed/analysis_panel_province_month_2024_2025.csv` | 912 | Panel TB bulanan + kovariat BPS pada tahun yang sama |
| `data/processed/tb_province_month_validation.json` | - | Manifest, checksum, cakupan, dan hasil QA |

## Catatan kualitas

Satu baris September 2024 dengan `fasyankes_provinsi_id = 37` berlabel `Papua`, sedangkan seluruh baris lain untuk ID 37, termasuk semua bulan 2025, berlabel `Papua Pegunungan`. Kurasi memakai ID sumber yang stabil untuk menetapkan `Papua Pegunungan`, mempertahankan label mentah, dan menandai `province_name_corrected = true`. Angka kasus tidak diubah.

Outcome 2025 belum aman dianggap final. Total `belum_ada_hasil` masih 112.593, jauh lebih besar daripada 2024 (9.044). Karena itu, perbandingan keberhasilan pengobatan 2025 dengan 2024 harus mengontrol kematangan kohort atau mengecualikan outcome yang masih pending.

## Sumber lain yang diperiksa

| Sumber | Hasil pemeriksaan | Keputusan |
|---|---|---|
| SATUSEHAT Data - Pemantauan Kasus Tuberkulosis | Seri nasional bulanan tersedia, tetapi ekspor geografis pada workbook publik mengosongkan provinsi/kabupaten | Dipakai hanya untuk tren nasional, tidak direkonstruksi menjadi provinsi |
| Profil Kesehatan Indonesia dan portal Satu Data daerah | Data provinsi/kabupaten yang ditemukan umumnya tahunan | Dipakai untuk validasi tahunan, bukan panel bulanan |
| Mendeley Data DOI 10.17632/k4dvwzdwsd.1 | Workbook TB memiliki sheet `Country Level`; sheet `Province Level` dan `District or City Level` kosong. Seri analisis lain adalah country-level triwulanan | Ditolak sebagai sumber provinsi-bulanan |
| Studi BMC Public Health 2025, PMC11809051 | Data SITB bulanan 2019-2022 untuk 87 kabupaten di Aceh, Sumatera Utara, Sumatera Barat, dan Riau; data mentah hanya tersedia melalui permintaan ke penulis | Valid sebagai rute tambahan, tetapi tidak memenuhi 38 provinsi dan belum dapat langsung diekstrak |
| Data Sampel BPJS Kesehatan | Berpotensi menghasilkan proksi klaim TB bulanan menggunakan ICD-10, tetapi portal meminta login dan hasilnya adalah utilisasi/klaim, bukan notifikasi SITB | Tidak dicampur ke target TB program tanpa akses dan definisi terpisah |
| BPS | Kovariat resmi provinsi tersedia tahunan/reference-period, bukan TB bulanan | Digabungkan menurut tahun tanpa interpolasi bulanan |

## Aturan analisis

1. Target yang tepat: `jumlah_pasien` / `treatment_started`, bukan `insidensi`.
2. Gunakan `outcome_pending` untuk menyaring kohort yang belum matang sebelum membandingkan treatment success.
3. BPS tetap annual: nilai 2024 diterapkan sebagai konteks seluruh bulan 2024, dan nilai 2025 untuk seluruh bulan 2025; jangan menyebutnya observasi bulanan.
4. Simpan snapshot, checksum, tanggal ekstraksi, dan URL karena dashboard dapat berubah.
5. Jangan gabungkan seri ini dengan notifikasi nasional SATUSEHAT seolah definisinya identik.

