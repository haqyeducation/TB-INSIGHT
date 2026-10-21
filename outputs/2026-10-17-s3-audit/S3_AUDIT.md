# Audit output Sprint 3 TB-INSIGHT

Tanggal audit: 17 Oktober 2026  
Lingkup: seluruh berkas dalam `Attachment/S3`, definisi task pada workbook ClickUp, panel analisis aktif, serta source frontend/backend yang dirujuk oleh laporan Erin.

## Keputusan umum

**S3 belum aman untuk ditutup atau dijadikan dasar M3.** Seluruh 10 task sudah memiliki output, tetapi belum ada task yang dapat ditandai final tanpa tindak lanjut. Hambatan utama adalah putusnya alur output Venedict ke model Stephen, kesalahan data kemiskinan BPS, keluaran peta yang belum dikemas, serta laporan frontend yang tidak cocok dengan source code yang tersedia.

## Status per task

| Task | Status audit | Keputusan utama |
|---|---|---|
| S3-VEN-01 | Revisi wajib | CSV lengkap 912 baris, 38 provinsi, 24 bulan, tanpa duplikat/missing. Lag 1–3 selaras untuk bulan yang dapat diperiksa. Namun generator `scripts/build_climate_lags_feature_matrix.py` yang diklaim tidak tersedia, sehingga lag awal 2024 yang memakai 2023 belum dapat direproduksi independen. |
| S3-VEN-02 | Tidak lulus | Laporan menyatakan tidak ada `|z| > 5`, padahal CSV memiliki 3 nilai dan maksimum precipitation z = 5,29005. Executive summary juga menyatakan maksimum +4,84. Klaim generator tersedia tidak sesuai isi repo. |
| S3-STE-01 | Tidak lulus | Hanya menjalankan lag 0–2 dan menandai lag 3 tidak tersedia, padahal `S3-VEN-01/climate_lags_v1.csv` memuat lag 3. Script membaca panel lama melalui path `D:\...`, bukan output dependensi Venedict. Acceptance “seluruh model pre-specified” belum terpenuhi. |
| S3-STE-02 | Tidak lulus sebagian | Struktur 9 model satu-interaksi-per-model, uncertainty, marginal contrast, dan catatan multiplicity tersedia. Namun 3 model poverty memakai data rusak: 60 baris dari 5 provinsi memiliki `poverty_pct > 100` (maksimum 25.898,55). Script juga memakai path lokal. Model poverty wajib dibatalkan dan dijalankan ulang setelah data dibetulkan. |
| S3-DAM-01 | Revisi wajib | Output LISA konsisten: 912 provinsi-bulan, 999 permutasi, FDR per bulan, 0 signifikan FDR. Namun boundary dan weights input tidak ada di repo/attachment, serta tidak ada hasil peta ter-render. Run belum dapat direproduksi dan acceptance visual belum dapat diperiksa. |
| S3-DAM-02 | Tidak lulus | Tidak ada file peta hasil render. Pemilihan kandidat mengurutkan `max-min` mentah antarvariabel dengan satuan berbeda, meskipun teks menyebut variasi relatif terhadap median. `poverty_pct` yang rusak ikut menjadikan peta kemiskinan kandidat. Boolean validasi skala/kausalitas diisi manual, bukan diuji. |
| S3-ERI-01 | Tidak dapat diverifikasi / tidak lulus | DOCX mengklaim halaman terpisah, peta Leaflet, filter URL, profil, unduhan, dan 18 tes. Source frontend yang tersedia masih satu halaman dengan anchor, satu grafik nasional, bar chart dan tabel; tidak ada implementasi peta, router, filter bersama, profil/unduhan, atau test script/test files. Source/diff aktual harus diserahkan. |
| S3-ERI-02 | Tidak dapat diverifikasi / tidak lulus | DOCX mengklaim halaman Sumber/Metode, ledger, checksum, unduhan metadata dan sembilan definisi. Source yang tersedia hanya memiliki satu section sumber dan limitation dari `/api/metadata`; fitur yang diklaim belum tampak. Bukti 18 tes juga tidak tersedia. |
| S3-ADZ-01 | Revisi setelah dependensi | Scope sudah benar: nasional, 38 provinsi, 2024–2025; baseline, lag, weights, 999 permutasi dan FDR ditulis. Namun dokumen menganggap QA Venedict lulus, mengulang klaim “pre-specified” yang belum memiliki bukti eksternal, dan mengutip output DAM yang belum reproducible. |
| S3-ADZ-02 | Revisi setelah dependensi | Audit novelty cukup kritis dan sudah menemukan korupsi `poverty_pct`. Namun dokumen mengulang alasan keliru bahwa lag 3 tidak tersedia; menempatkan forecasting/ILP sebagai blokir S3-STE-02 padahal bukan scope task itu; serta menyatakan dashboard tanpa bukti walaupun paket Erin mengklaim sebaliknya. Harus disinkronkan setelah output teknis diperbaiki. |

## Temuan lintas task yang memblokir penutupan S3

1. **Output dependensi tidak benar-benar dipakai.** Stephen membaca `analysis_panel_tb_climate_disaster_2024_2025.csv` lama, bukan `climate_lags_v1.csv`; akibatnya lag 3 yang dibuat Venedict dilewati.
2. **QA fitur salah secara faktual.** Terdapat tiga nilai z-score presipitasi di atas 5, berlawanan dengan status PASS dan angka ringkasan.
3. **Data kemiskinan rusak.** Lima provinsi memiliki nilai di atas 100% pada satu tahun. Ini membatalkan model interaksi kemiskinan dan peta kerentanan kemiskinan.
4. **Spatial pipeline belum portabel.** Boundary 38 provinsi dan weights Queen+bridge v2 yang dipanggil Rmd tidak tersedia pada paket/repo yang diaudit.
5. **Keluaran UI tidak cocok dengan laporan.** Berkas implementasi yang mendukung fitur dan 18 tes tidak tersedia. Laporan perubahan saja tidak cukup sebagai deliverable frontend.
6. **Naskah mengikuti output yang belum lolos.** Methods dan Results shell tidak boleh dibekukan sebelum data, model, spatial output, dan frontend diselaraskan.

## Urutan perbaikan

1. Venedict menyerahkan generator fitur, memperbaiki QA z-score, dan membekukan `climate_lags_v1.csv` beserta checksum.
2. Data Scientist memperbaiki mapping `poverty_pct` pada sumber BPS dan membangun ulang panel.
3. Stephen mengganti path relatif, membaca output Venedict, menjalankan lag 0–3 sesuai task, lalu menjalankan ulang seluruh interaksi setelah panel diperbaiki.
4. Dame menyertakan boundary/weights berversi, menjalankan ulang dari panel baru, mengekspor peta PNG/PDF/HTML, dan memperbaiki pemilihan kandidat menggunakan ukuran terstandardisasi atau kriteria substantif per kelompok variabel.
5. Erin menyerahkan source commit/diff aktual dan test suite. Klaim DOCX harus dicocokkan dengan fitur yang benar-benar tersedia.
6. Adzki merevisi Methods dan Results shell terakhir, setelah seluruh output upstream memiliki ID, checksum, dan status review yang jelas.

## Gate kelulusan S3

S3 baru aman ditutup apabila seluruh pipeline dapat dijalankan dari path repo relatif; panel dan feature matrix memiliki checksum; tidak ada nilai sosial di luar rentang; semua model pre-specified dijalankan atau memiliki alasan skip yang benar; map outputs tersedia dan dapat diperiksa; frontend source cocok dengan laporan serta tes; dan naskah hanya mengutip output yang sudah disetujui.
