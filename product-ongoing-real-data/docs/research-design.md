# Desain riset dengan panel SITB 24 bulan

Tanggal penyusunan: 12 Agustus 2026

## Rekomendasi utama

Tema terbaik adalah **climate-related disruption of TB treatment access and cohort outcomes across Indonesian provinces**.

Pertanyaan utama:

> Apakah anomali curah hujan, panas, dan kejadian banjir berkaitan dengan perubahan jumlah pasien yang memulai pengobatan TBC sensitif obat di tingkat provinsi, dan apakah hubungan tersebut lebih kuat pada provinsi dengan kerentanan sosial serta kapasitas layanan yang lebih rendah?

Penelitian harus dibingkai sebagai analisis layanan/program TB, bukan penelitian insidensi biologis. Variabel SITB `jumlah_pasien` adalah kohort yang mulai pengobatan pada bulan tertentu.

## Mengapa ini lebih kuat daripada seasonality biasa

1. Indonesia tidak memiliki satu musim hujan yang seragam. Menggunakan anomali cuaca setiap provinsi terhadap normal klimatologinya lebih informatif daripada dummy `musim hujan` nasional.
2. Hujan ekstrem dan banjir memiliki mekanisme langsung terhadap akses: transportasi, jam layanan, kehadiran petugas, diagnosis, dan pengambilan obat.
3. Panel 38 provinsi memberikan 912 observasi. Informasi utama berasal dari variasi cuaca antardaerah dalam bulan yang sama, bukan dari menganggap 24 bulan sebagai time series panjang.
4. Outcome SITB memungkinkan pemisahan tiga fenomena: jumlah mulai pengobatan, outcome merugikan, dan kematangan kohort (`belum_ada_hasil`).
5. Integrasi SITB, data iklim gridded, kejadian bencana BNPB, dan kerentanan BPS pada 38 provinsi tampaknya belum menjadi desain umum pada studi TB Indonesia yang ditemukan.

Novelty harus ditulis sebagai **novel integration and framing**, bukan klaim “studi pertama” sebelum systematic search formal selesai.

## Dataset yang digunakan

| Domain | Variabel | Sumber | Resolusi |
|---|---|---|---|
| TB | Mulai pengobatan, sembuh, lengkap, LTFU, meninggal, gagal, tidak dievaluasi, outcome pending | TB Dashboard SITB | Provinsi-bulan, 2024-2025 |
| Iklim utama | Total precipitation, suhu 2 m, kelembapan/dew point, soil moisture | ERA5-Land/ERA5 Copernicus | Grid-bulan; diagregasi area-weighted ke provinsi |
| Validasi hujan | Curah hujan | CHIRPS final | Grid-bulan; diagregasi ke provinsi |
| Gangguan aktual | Banjir, longsor, cuaca ekstrem, penduduk terdampak | BNPB Satu Data Bencana/DIBI | Kejadian; diagregasi ke provinsi-bulan |
| Kerentanan | Penduduk, kepadatan, kemiskinan, sanitasi | BPS | Provinsi-tahun |
| Kapasitas layanan opsional | Puskesmas, rumah sakit, tenaga kesehatan atau fasilitas pelapor aktif | Kemenkes/SITB | Provinsi-tahun atau provinsi-bulan jika tersedia |

Sumber primer:

- SITB 2024: https://tbdashboard.sitb.id/ss_data_tbc03so_2024_provinsi_bulanan_list.php
- SITB 2025: https://tbdashboard.sitb.id/ss_data_tbc03so_2025_provinsi_bulanan_list.php
- ERA5 monthly: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means
- CHIRPS: https://www.chc.ucsb.edu/data/chirps3
- BNPB: https://data.bnpb.go.id/dataset/data-bencana-indonesia
- BMKG pembanding: https://dataonline.bmkg.go.id/

## Definisi outcome

### Outcome primer

`treatment_started_it`: jumlah pasien TBC sensitif obat yang mulai pengobatan di provinsi `i` pada bulan `t`.

Model count memakai `log(population_it)` sebagai offset. Interpretasi menjadi perubahan relatif tingkat mulai pengobatan per penduduk, bukan insidensi TB.

### Outcome sekunder

- `pending_share = belum_ada_hasil / jumlah_pasien`
- `adverse_known_share = (lost_to_follow_up + meninggal + gagal) / (jumlah_pasien - belum_ada_hasil)`
- `success_known_share = (sembuh + pengobatan_lengkap) / (jumlah_pasien - belum_ada_hasil)`
- `not_evaluated_share = tidak_dievaluasi_pindah / jumlah_pasien`

Analisis outcome dibatasi pada kohort matang, misalnya `pending_share < 5%`, atau pada kohort 2024. Angka 5% harus diuji pada sensitivity analysis, bukan diperlakukan sebagai standar klinis universal.

## Definisi paparan yang disarankan

Jangan memakai curah hujan mentah sebagai satu-satunya paparan. Bentuk variabel berikut per provinsi-bulan:

- anomali curah hujan terhadap normal provinsi dan bulan kalender 1991-2020;
- persentil hujan ekstrem, misalnya di atas P90 historis provinsi-bulan;
- anomali suhu dan humidex/dew point;
- jumlah kejadian banjir dan log(1 + penduduk terdampak);
- interaksi hujan ekstrem x banjir untuk membedakan exposure meteorologis dari gangguan nyata;
- interaksi gangguan x kemiskinan/kepadatan/sanitasi sebagai effect modification.

Normal klimatologi dapat dihitung dari ERA5/CHIRPS historis meskipun outcome TB hanya tersedia 2024-2025. Ini tidak menambah observasi TB, tetapi membuat pengukuran “ekstrem” lebih valid.

## Strategi analisis

### Tahap 1 — pola musiman deskriptif

- Standardisasi `treatment_started` terhadap populasi.
- Estimasi harmonic sederhana: sine dan cosine 12 bulanan.
- Estimasi amplitude dan peak month dengan partial pooling antardaerah.
- Kelompokkan provinsi berdasarkan rezim monsun/curah hujan historis, bukan berdasarkan pulau secara arbitrer.

Hasil tahap ini bersifat deskriptif. Dua siklus tahunan belum cukup untuk mengklaim seasonality stabil jangka panjang.

### Tahap 2 — model panel utama

Gunakan Poisson pseudo-maximum likelihood atau negative binomial:

```text
E(Y_it) = exp(
  province_FE_i
  + month_year_FE_t
  + beta1 * rainfall_anomaly_it
  + beta2 * heat_anomaly_it
  + beta3 * flood_it
  + lag terms
  + log(population_it)
)
```

`month_year_FE` mengontrol gangguan nasional pada bulan yang sama. Koefisien iklim diidentifikasi dari perbedaan lokal antardaerah. Batasi lag utama ke 0-2 bulan agar jumlah parameter tidak berlebihan. Standard error dikelompokkan menurut provinsi; dengan 38 cluster, tambahkan wild-cluster bootstrap.

### Tahap 3 — kerentanan sebagai modifier

Uji satu interaksi per model, bukan memasukkan seluruh interaksi sekaligus:

- hujan ekstrem x kemiskinan;
- banjir x kepadatan;
- banjir x kapasitas layanan;
- cuaca ekstrem x sanitasi.

Hasil dilaporkan sebagai marginal effect dengan interval kepercayaan, bukan hanya p-value.

### Tahap 4 — outcome kohort

Outcome pengobatan terjadi selama beberapa bulan setelah pasien mulai terapi. Karena itu, paparan yang relevan adalah cuaca/gangguan selama jendela follow-up, bukan hanya cuaca pada bulan mulai pengobatan.

Untuk kohort matang 2024:

- hitung hujan ekstrem/banjir kumulatif bulan 0-5 setelah mulai pengobatan;
- modelkan adverse outcome menggunakan binomial atau beta-binomial;
- lakukan sensitivity analysis jendela 0-2, 0-5, dan 0-6 bulan;
- jangan menggunakan kohort akhir 2025 sebelum outcome pending cukup rendah.

Ini merupakan komponen yang berpotensi paling baru karena menyelaraskan paparan iklim dengan periode perawatan, bukan menghubungkan cuaca bulan diagnosis secara naif.

## Validasi dan falsification tests

- Bandingkan hujan ERA5 dengan CHIRPS; kesimpulan utama harus tidak berubah arah.
- Placebo lead: cuaca 1-2 bulan setelah `treatment_started` tidak semestinya “memprediksi” inisiasi pengobatan yang sudah terjadi.
- Ulangi model tanpa DKI Jakarta dan provinsi Papua baru.
- Gunakan leave-one-province-out influence analysis.
- Periksa Moran's I residual; tambahkan spatial error/random effect hanya bila residual benar-benar spasial.
- Laporkan false discovery rate jika banyak paparan/interaksi diuji.
- Bedakan missing, zero, dan outcome pending.
- Jangan menyebut asosiasi sebagai efek kausal tanpa desain identifikasi tambahan.

## Hal yang tidak direkomendasikan

- ARIMA/LSTM/Prophet per provinsi: hanya 24 titik per provinsi.
- Forecast operasional jangka panjang: dua siklus tahunan tidak memadai.
- Mengklaim curah hujan menyebabkan transmisi TB dari data mulai pengobatan.
- Memasukkan banyak lag, spline, dan interaksi sekaligus; model akan overfit.
- Membandingkan treatment success mentah 2024 vs 2025 saat outcome 2025 belum matang.
- Mengulang nilai BPS tahunan ke setiap bulan lalu memperlakukannya sebagai 24 observasi independen.

## Opsi penelitian dan prioritas

| Opsi | Novelty | Kelayakan | Risiko | Keputusan |
|---|---:|---:|---:|---|
| Seasonality kalender saja | Sedang | Tinggi | Dua siklus terlalu pendek | Analisis pendahuluan |
| Cuaca terhadap “insidensi TB” | Tampak tinggi | Rendah | Salah definisi outcome | Tolak |
| Anomali iklim terhadap mulai pengobatan | Tinggi | Tinggi | Ekologis, lag terbatas | Utama |
| Banjir sebagai gangguan akses | Tinggi | Tinggi jika BNPB lengkap | Reporting bencana heterogen | Utama bersama iklim |
| Iklim selama follow-up terhadap outcome kohort | Sangat tinggi | Sedang | Perlu maturity filter | Analisis sekunder unggulan |
| Ramadan/libur terhadap layanan | Menarik | Sedang-rendah | Hanya dua observasi Ramadan | Sensitivity/exploratory |
| Machine-learning forecasting | Rendah secara ilmiah | Rendah | Overfit | Tolak saat ini |

## Judul yang disarankan

Bahasa Inggris:

> Climate anomalies, flood-related service disruption, and tuberculosis treatment initiation across 38 Indonesian provinces: a monthly ecological panel study, 2024-2025

Alternatif berfokus outcome:

> Weather disruptions during treatment follow-up and cohort outcomes of drug-susceptible tuberculosis across Indonesian provinces

## Referensi jurnal terindeks Scopus

Jurnal di bawah tercakup Scopus; status indeks tetap perlu dicek kembali pada tanggal submission karena coverage database dapat berubah.

1. Saputra A, Wichaidit W, Kesuma ZM, et al. Spatio-temporal distribution of COVID-19 cases and tuberculosis in four provinces of Sumatra Islands, Indonesia. *BMC Public Health*. 2025;25:529. https://doi.org/10.1186/s12889-025-21754-z
2. MacPherson P, et al. Tuberculosis case notifications in Malawi have strong seasonal and weather-related trends. *Scientific Reports*. 2021;11. https://doi.org/10.1038/s41598-021-84124-w
3. Gashu Z, Jerene D, Datiko DG, et al. Seasonal patterns of tuberculosis case notification in the tropics of Africa: a six-year trend analysis in Ethiopia. *PLOS ONE*. 2018;13(11):e0207552. https://doi.org/10.1371/journal.pone.0207552
4. Zhang Y, et al. Association between averaged meteorological factors and tuberculosis risk: a systematic review and meta-analysis. *Environmental Research*. 2022;212:113279. https://doi.org/10.1016/j.envres.2022.113279
5. Gasparrini A, Armstrong B, Kenward MG. Distributed lag non-linear models. *Statistics in Medicine*. 2010;29(21):2224-2234. https://doi.org/10.1002/sim.3940
6. Tosepu R, Sani A, Effendy DS, et al. The association between climate variables and tuberculosis in Kolaka District, Southeast Sulawesi Province, Indonesia, 2013-2020: a Bayesian autoregressive model. *F1000Research*. 2024;12:1507. https://doi.org/10.12688/f1000research.138859.2
7. Puspita T, et al. Spatial variation of tuberculosis risk in Indonesia 2010-2019. *Health Science Journal of Indonesia*. 2022. Gunakan sebagai konteks spasial Indonesia dan verifikasi metadata/index coverage pada Scopus sebelum sitasi administratif final.

Referensi kebijakan tambahan, bukan artikel Scopus:

- WHO. *Tuberculosis and climate change*. 2025. https://www.who.int/publications/i/item/9789240109940

## Kesimpulan operasional

Dengan resource sekarang, target publikasi paling realistis adalah studi panel ekologis nasional mengenai **akses memulai pengobatan saat terjadi anomali iklim dan banjir**, ditambah analisis outcome pada kohort yang sudah matang. Desain ini lebih kuat daripada forecasting dan lebih jujur daripada menyebut data sebagai insidensi. Prioritas akuisisi berikutnya adalah ERA5/CHIRPS 1991-2025, BNPB 2024-2025, dan satu indikator kapasitas layanan provinsi.
