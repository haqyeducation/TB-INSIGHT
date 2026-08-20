# Product brief — Demo Synthetic

## Tujuan

Menyediakan prototype yang stabil untuk menunjukkan seperti apa TB-INSIGHT saat digunakan oleh pengelola program: dari overview kota, eksplorasi peta, pembukaan profil kecamatan, sampai simulasi skenario sumber daya.

## Pengguna utama

- tim product dan frontend;
- dosen/pembimbing saat menilai konsep produk;
- calon stakeholder saat memberi masukan atas kebutuhan UI;
- engineer yang menguji API dan interaksi dashboard.

## Nilai yang didemonstrasikan

1. Informasi wilayah dapat dijelajahi melalui peta dan profil.
2. Sistem dapat menampilkan alert serta proyeksi.
3. Pengguna dapat mencoba skenario anggaran dan tenaga kesehatan.
4. Sumber, definisi, dan status data harus terlihat jelas.

## Batas produk

Prototype ini tidak menguji validitas epidemiologi. Skor risiko, performa model, forecast, kebutuhan tenaga kesehatan, dan biaya hanyalah simulasi. Keberhasilan demo dinilai dari kejelasan alur dan usability, bukan akurasi angka.

## Roadmap demo

### Tahap 1 — Stabilkan demo

- pastikan seluruh halaman menampilkan label synthetic;
- selesaikan smoke test frontend, backend, peta, dan optimizer;
- hilangkan klaim yang menyerupai rekomendasi kebijakan nyata.

### Tahap 2 — Jadikan UI reusable

- pisahkan komponen peta, filter, kartu indikator, dan provenance;
- buat kontrak API yang tidak bergantung pada nama kolom dummy;
- siapkan design tokens dan state kosong/loading/error.

### Tahap 3 — Transfer fitur terpilih

- pindahkan hanya komponen UI yang telah ditinjau ke product ongoing;
- mapping setiap komponen ke variabel resmi dan definisinya;
- lakukan review data dan metodologi sebelum sebuah fitur diaktifkan.

## Definition of done

- demo dapat dijalankan lokal dari README;
- banner synthetic selalu terlihat;
- tidak ada klaim data resmi atau keputusan nyata;
- seluruh interaksi utama memiliki state error yang jelas;
- tidak ada dependency, cache, atau build output yang dibagikan.

