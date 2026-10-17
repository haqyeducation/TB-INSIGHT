# TB-INSIGHT frontend

Dashboard React/Vite dengan enam halaman terpisah: Ringkasan, Tren, Peta, Provinsi, Metode, dan Sumber. Navigasi menggunakan hash URL agar tombol kembali dan tautan dengan filter tetap berfungsi. Tidak ada data demo atau angka sintetis.

### Persiapan snapshot

Dari folder `product-ongoing-real-data`, jalankan ulang saat input resmi berubah:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_dashboard.py --reference-dir "C:\Users\ACER\OneDrive\Dokumen\IRISEARCH\LONGTERM 2026 TB_INSIGHT" --climate-zip "C:\Users\ACER\Downloads\clickup-attachments-2026-10-11-16-48.zip"
```

Sesuaikan lokasi arsip jika dipindah. Script memakai dependensi pada `requirements-analysis.txt`, termasuk Shapely, untuk membaca kohort, panel konteks, ledger sumber, batas BIG, dan lampiran Dame; menyimpan snapshot serta GeoJSON di `frontend/public`. Data sumber tidak diubah. Kemiskinan di luar 0–100% disembunyikan dan dicatat. Kode batas Papua dicocokkan melalui identitas provinsi, bukan langsung digabung berdasarkan kode sumber. Sebanyak 539 bagian batas sumber digabung menjadi 38 geometri provinsi untuk tampilan agar garis internal tidak mengaburkan peta. Komponen poligon diperbaiki topologinya; komponen yang sudah kolaps menjadi garis/titik tidak menjadi area peta. Pengolahan tampilan ini dicatat pada metadata.

### Menjalankan

Backend (dari folder produk):

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

Frontend (terminal lain, dari folder `frontend`):

```powershell
npm ci
npm run dev
```

Build produksi:

```powershell
npm run build
```

Frontend mencoba `/api/dashboard` melalui proxy Vite ke port 8000. Jika backend belum tersedia, frontend memakai snapshot resmi di `/data/dashboard-snapshot.json` dengan label eksplisit. Keduanya snapshot yang sama, bukan pembaruan sumber secara langsung. Setelah mengubah backend, hentikan proses backend lama lalu jalankan kembali. Endpoint alpha ini tidak mengklaim seluruh rancangan `/api/v1/*` pada kontrak sudah tersedia.

### Fitur dan batas data

- Filter wilayah, rentang bulan, bulan fokus, jumlah/rate tersimpan dalam URL.
- Tren memiliki tooltip, penanda provisional, pembanding maksimal tiga provinsi, kalender bulanan, dan tabel.
- Peta memiliki sembilan layer, legenda tetap, zoom/reset, navigasi bulan dan putar/jeda setiap 1,5 detik, perbandingan peta, serta detail provinsi lewat klik wilayah, keyboard, atau tabel. Persistence tetap merangkum seluruh 24 bulan dan tidak dianimasikan.
- Filter bertahap dapat dilipat, memiliki pilihan rentang cepat, serta mempertahankan posisi baca ketika bulan berubah. Animasi putar memperbarui URL tanpa menambah entri riwayat setiap bulan.
- Visual utama dapat diperbesar; Escape menutupnya dan mengembalikan fokus. Perubahan halaman, grafik, dan warna peta memakai transisi singkat yang mengikuti preferensi reduced motion.
- Profil provinsi memuat outcome, konteks sosial, iklim, bencana, hasil spasial, dan pembanding nasional pada bulan yang sama.
- CSV dan metadata sumber/filter/versi memiliki tombol unduh terpisah agar browser tidak memblokir unduhan kedua. Halaman Sumber juga menyediakan metadata seluruh snapshot.
- LISA bulanan dan persistence berasal dari lampiran Dame. Versi input analisisnya belum direkonsiliasi dengan kohort aktif; periode dan catatan ini ditampilkan.
- Forecast, interval ketidakpastian, model tervalidasi, dan kapasitas fasilitas ditampilkan sebagai ruang visual dengan catatan data yang masih diperlukan, tanpa mengarang nilai.
- Rate nasional menggunakan rasio total pasien terhadap total penduduk. Persentase pending menggunakan rasio total, bukan rerata persentase provinsi. Sosial mempertahankan periode survei/tahun rujukan.
- Nol tercatat, belum tersedia, dan belum valid dibedakan. Peta memakai arsiran diagonal untuk data hilang dan silang untuk data tidak valid. N/A hanya untuk indikator yang dinyatakan tidak berlaku oleh metadata, bukan pengganti nilai hilang.

### Gaya visual

Palet pada `src/theme.js`: Azure Mist `#E2F5F3` sebagai latar, Icy Blue `#A4CBE3`, Strong Cyan `#4DD4CD`, Twilight Indigo `#333C77`, dan Ink Black `#001B29`. Permukaan kartu putih; teks sekunder menggunakan turunan gelap agar tetap kontras. Warna grafik numerik berurutan, anomali divergen, dan kategori spasial memiliki legenda tersendiri.

Judul sans besar, aksen serif miring, ruang lega, dan kontrol membulat mengikuti inspirasi [Maven Clinic](https://www.mavenclinic.com/). Font publik DM Sans dan Instrument Serif dimuat melalui Google Fonts dengan fallback Arial/Georgia, tanpa menyalin font milik Maven. Pola grafik/peta/tabel serta sumber dekat visual mengikuti referensi pengguna WHO, Our World in Data, IHME, PAHO, dan UNICEF.

### Pemeriksaan

S3-ERI-02 menambahkan metadata sumber, satuan, pemakaian, tanggal yang tercatat, checksum, kamus indikator, serta catatan yang dapat dibuka dekat visual utama. Tanggal akses historis yang tidak memiliki bukti tetap `null` dan ditampilkan sebagai **Belum tercatat**. Waktu pada olahan SITB dan pemeriksaan tautan memiliki label terpisah. Lihat `docs/design/s3-eri-02-implementation.md` untuk acuan, audit tanggal, dan langkah pembaruan metadata tanpa mengubah nilai kohort.

```powershell
node --test tests/*.test.js
npm run lint
npm run build
```

Tes memeriksa agregasi, missing/zero/invalid/N/A, gap bulan, skala peta, periode spasial, pemetaan kode Papua, serta rasio kontras teks utama dan sekunder pada permukaan yang digunakan. Build produksi menyertakan snapshot dan batas provinsi. Hasil alpha belum menggantikan review metode, rekonsiliasi input Dame, atau manifest freeze yang disetujui.
