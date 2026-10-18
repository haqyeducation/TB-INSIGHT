# M2 — review output S2 dan arahan menuju S3

**Keputusan: HOLD untuk sign-off M2 (16 September 2026).** Sepuluh paket S2 sudah diterima dan ditelaah, tetapi angka, model, peta, desain, dan naskah belum seluruhnya berasal dari versi input/output yang sama. S3 dapat dimulai **bertahap untuk pekerjaan persiapan**, bukan untuk mengunci hasil inferensial atau memublikasikan dashboard. Rincian temuan per paket dan arahan per task ada pada lampiran `TB_INSIGHT_M2_to_S3_Direction.xlsx`.

## Koreksi yang wajib sebelum M2 ditutup

1. **Satu panel dan jejak reproduksi.** Bekukan panel provinsi-bulan 2024–2025 beserta checksum, codebook, definisi outcome, dan aturan status provisional. Ganti rujukan `release_v1` yang belum ada; simpan generator serta input/output berversi di repo.
2. **Deskriptif Venedict.** Bedakan *pending share* rerata provinsi dari rasio nasional tertimbang; perbaiki klaim kematangan cohort 2024. Pisahkan flag provenance/kualitas dari outlier statistik dan rekonsiliasi daftar outlier nasional dengan profil provinsi.
3. **Model Stephen.** Jadikan `S2-STE-01/ver2` versi kanonik: tiga paparan primer terpisah, model gabungan hanya sensitivitas. Hilangkan path lokal; jalankan ulang diagnostik S2-STE-02 untuk masing-masing model primer dan sensitivitas, dengan `model_id`, sampel, dan input yang konsisten.
4. **Spasial Dame.** Masukkan boundary dan spatial weights berversi sehingga Moran/LISA dapat dijalankan ulang; jelaskan dua bridge tambahan dan laporkan sensitivitas bobot. Hasil LISA agregat tidak menunjukkan provinsi signifikan setelah FDR; jangan klaim hotspot persisten sebelum analisis bulanan S3.
5. **Produk dan naskah.** Finalkan PDF wireframe Erin dan tandai angka HTML sebagai fixture; verifikasi serta setujui kontrak UI terhadap panel nyata. Tulis ulang Methods Adzki karena draft S2 masih menyebut Surabaya/31 kecamatan, bukan studi 38 provinsi × 24 bulan. Rekonsiliasi naskah hasil ke tabel kanonik setelah deskriptif dan model diperbaiki.

## Urutan izin mulai S3

- **Boleh mulai sekarang, terbatas:** Venedict mengaudit rancangan fitur iklim/lag; Dame menetapkan metode persistensi hotspot; Erin membangun *frontend shell* dan state loading/error tanpa angka contoh sebagai hasil nyata; Adzki menulis ulang kerangka Methods nasional.
- **Tunggu QA input:** S3-VEN-02 menunggu matriks fitur S3-VEN-01; S3-STE-01 menunggu QA fitur dan model S2 yang sinkron; S3-DAM-02 menunggu QA fitur serta S3-DAM-01; integrasi data frontend menunggu kontrak dan output spasial disetujui.
- **Tunggu hasil tervalidasi:** S3-STE-02 mengikuti S3-STE-01; Methods final S3-ADZ-01 mengikuti QA fitur/spasial; Results shell S3-ADZ-02 mengikuti model interaksi dan Methods final. Semua klaim tetap observasional, bukan kausal.

**Gate M2 lulus jika:** seluruh pemilik task menyerahkan file final di path deliverable, run ulang dari input berversi berhasil, angka/label/status data konsisten lintas CSV–model–peta–UI–naskah, dan reviewer menyetujui pengecualian atau keterbatasan yang masih tersisa. Task S3 mengikuti `S3 Direction` pada lampiran Excel, bukan bergantung pada label “M2” saja.
