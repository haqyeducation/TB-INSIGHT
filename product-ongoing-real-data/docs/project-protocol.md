# Draft Proyek TB-INSIGHT: Anomali Iklim dan Inisiasi Pengobatan TB di Indonesia

## Keputusan desain

Proyek dilanjutkan pada skala **38 provinsi x bulan, Januari 2024-Desember 2025**. Fokus utama yang paling defensibel dengan data saat ini adalah hubungan antara **anomali iklim** dan **jumlah pasien yang memulai pengobatan TB sensitif obat**, bukan insidensi TB. Kejadian bencana BNPB dipakai hanya sebagai analisis sensitivitas karena panel bulanannya berasal dari tabel operasional yang tidak sepenuhnya konsisten dengan kompilasi tahunan resmi.

Seluruh variabel wajib pada panel utama telah terisi: 912 baris, 38 provinsi, 24 bulan, tanpa duplikasi kunci dan tanpa missing pada TB, populasi, kepadatan, sanitasi, kemiskinan, temperatur, kelembapan, curah hujan, atau jumlah kejadian bencana. Tidak ada data sintetis pada panel final.

## Judul kerja

**Climate Anomalies and Monthly Tuberculosis Treatment Initiation Across Indonesian Provinces: A Data-Maturity-Aware Ecological Panel Study, 2024-2025**

Judul Indonesia:

**Anomali Iklim dan Inisiasi Pengobatan Tuberkulosis Bulanan di 38 Provinsi Indonesia: Studi Panel Ekologis yang Memperhitungkan Kematangan Data, 2024-2025**

## Kebaruan yang realistis

1. Eksposur tidak memakai musim atau curah hujan mentah, melainkan anomali dan z-score provinsi-bulan terhadap normal klimatologis 1991-2020. Ini memisahkan kondisi yang tidak biasa dari pola musim reguler.
2. Outcome adalah inisiasi pengobatan programatik bulanan, sehingga interpretasi diarahkan pada gabungan deteksi, akses layanan, dan pelaporan - bukan klaim bahwa cuaca langsung menyebabkan infeksi TB.
3. Analisis membedakan cohort outcome yang matang dan provisional melalui `pending_share` dan `cohort_maturity_flag`.
4. Model memakai fixed effect provinsi dan fixed effect bulan-tahun nasional, sehingga membandingkan perubahan dalam provinsi setelah mengendalikan faktor tetap provinsi dan shock nasional tiap bulan.
5. Bencana dibandingkan terhadap dua produk BNPB: tabel kejadian operasional bulanan dan workbook kompilasi tahunan. Ketidaksesuaian tidak disembunyikan, tetapi dijadikan batas inferensi.

Kebaruan ini lebih kuat dan lebih jujur daripada sekadar memprediksi angka TB dari 24 titik waktu atau mengklaim seasonality dengan hanya dua siklus tahunan.

## Pertanyaan riset

### Pertanyaan primer

Apakah anomali temperatur, kelembapan, dan curah hujan pada bulan berjalan atau rerata tiga bulan berkaitan dengan perubahan jumlah pasien yang memulai pengobatan TB sensitif obat dalam provinsi yang sama?

### Pertanyaan sekunder

1. Apakah hubungan tersebut lebih kuat pada provinsi dengan kemiskinan lebih tinggi, sanitasi lebih rendah, atau kepadatan lebih tinggi?
2. Apakah hasil tetap konsisten setelah menambahkan kejadian hidrometeorologi BNPB sebagai kovariat sensitivitas?
3. Apakah cohort yang memulai terapi pada kondisi iklim ekstrem menunjukkan proporsi outcome tertunda atau adverse outcome yang berbeda, hanya pada cohort yang cukup matang?
4. Apakah pola deskriptif kalender menunjukkan musim yang serupa pada 2024 dan 2025? Analisis ini bersifat deskriptif karena hanya tersedia dua siklus tahunan.

## Hipotesis yang dipraregistrasikan

- H1: anomali hujan ekstrem berkaitan dengan perubahan inisiasi pengobatan pada bulan yang sama sampai dua bulan berikutnya melalui akses layanan, mobilitas, dan pelaporan.
- H2: efek anomali lebih besar pada provinsi dengan kerentanan struktural lebih tinggi.
- H3: hasil bencana hanya dianggap mendukung jika arah estimasi konsisten dengan model iklim; bencana tidak digunakan untuk menggantikan eksposur iklim utama.
- H4: tidak ada klaim kausal atau biologis langsung tanpa data onset gejala, tanggal diagnosis, mobilitas, dan kapasitas fasilitas kesehatan.

## Inventaris data final

| Data | Unit | Cakupan | Status ekstraksi | Peran |
|---|---|---:|---|---|
| SITB outcome pengobatan | provinsi-bulan | 2024-2025; 912 cohort | Lengkap; seluruh kategori outcome seimbang dengan total pasien | Outcome primer dan sekunder |
| BPS populasi dan kepadatan | provinsi-tahun | 2024-2025 | Lengkap | Offset populasi dan kovariat |
| BPS sanitasi layak | provinsi-tahun | Susenas 2024-2025 | Lengkap | Kerentanan struktural |
| BPS kemiskinan | provinsi-tahun | Susenas Maret 2024 dan Maret 2025 | Lengkap | Kerentanan struktural |
| NASA POWER/MERRA-2 | grid-bulan ke provinsi-bulan | 1981-2025; output 2024-2025 | Lengkap | Temperatur, kelembapan, presipitasi, normal, anomali, lag |
| BIG batas provinsi | poligon | 38 provinsi | Lengkap; generalisasi dan perbaikan topologi tercatat | Agregasi spasial iklim |
| BNPB tabel kejadian | kejadian ke provinsi-bulan | 2024-2025 | 7.164 raw, 21 duplikat substantif dihapus, 7.143 curated | Sensitivitas |
| BNPB workbook tahunan | provinsi-tahun | 2024-2025 | Lengkap | Benchmark QA BNPB |

Sumber utama tersedia pada [SITB](https://tbdashboard.sitb.id/), [BPS](https://www.bps.go.id/), [NASA POWER Monthly API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/), [BIG](https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/BATAS_WILAYAH/MapServer/12), dan [BNPB](https://data.bnpb.go.id/dataset/data-bencana-indonesia).

## Berkas siap analisis

- `data/processed/analysis_panel_tb_climate_disaster_2024_2025.csv`: panel final satu baris per provinsi-bulan.
- `data/processed/analysis_panel_tb_climate_codebook.csv`: definisi variabel.
- `data/processed/project_source_ledger.csv`: asal, status, dan keterbatasan setiap sumber.
- `data/processed/analysis_panel_tb_climate_validation.json`: QA panel final.
- `data/processed/climate_province_month_official.csv`: iklim, normal 1991-2020, anomali, lag 1-2 bulan, dan rerata tiga bulan.
- `data/processed/climate_province_climatology_1991_2020.csv`: normal dan simpangan baku provinsi-bulan kalender.
- `data/processed/bnpb_disaster_events_2024_2025_official.csv`: kejadian BNPB terdeduplikasi.
- `data/processed/bnpb_disaster_province_month_official.csv`: agregasi bencana provinsi-bulan.
- `data/processed/bnpb_disaster_annual_reconciliation.csv`: perbandingan operasional versus workbook tahunan.

## Definisi outcome

### Primer

`jumlah_pasien`: jumlah pasien yang memulai pengobatan TB sensitif obat pada provinsi dan bulan tertentu. Model count menggunakan `log_population_offset`.

### Sekunder

- `treatment_success_known_share`: sembuh + pengobatan lengkap dibagi outcome yang sudah diketahui.
- `adverse_known_share`: lost to follow-up + meninggal + gagal dibagi outcome yang sudah diketahui.
- `pending_share`: proporsi cohort yang belum memiliki outcome.

Analisis outcome dibatasi pada `cohort_maturity_flag = mature_le_5pct_pending`, dengan threshold 10% sebagai sensitivitas. Tahun 2025 tidak boleh dianalisis seolah-olah final: rata-rata pending share 15,39%, dibanding 2,80% pada 2024.

## Definisi eksposur

- `temperature_c_z`, `relative_humidity_pct_z`, `precipitation_mm_z`: deviasi standar dari normal provinsi dan bulan kalender 1991-2020.
- lag 1 dan 2 bulan serta `*_mean_lag0_2` sudah tersedia.
- `heavy_rain_anomaly` dan `hot_anomaly`: indikator minimal +1 SD.
- `hydrometeorological_events`: banjir, longsor, cuaca ekstrem, kekeringan, karhutla, serta gelombang pasang/abrasi dari BNPB.

Presipitasi NASA POWER bulanan awalnya berupa rata-rata mm/hari; `precipitation_mm` telah dikonversi menjadi total bulanan dengan jumlah hari kalender.

## Strategi analisis

### 1. Deskriptif dan QA

- Plot jumlah pasien dan rate per 100.000 per provinsi dan bulan.
- Plot eksposur sebagai anomali, bukan hanya nilai mentah.
- Bandingkan distribusi 2024 dan 2025.
- Tampilkan peta grid-cell method dan tandai provinsi kecil yang memakai grid terdekat.
- Laporkan pending outcome per cohort sebelum menampilkan success/adverse outcome.

### 2. Model primer

Gunakan Poisson pseudo-maximum likelihood:

`E(Y_it) = exp(beta * climate_it + province_FE_i + period_FE_t + log(population_it))`

Dengan:

- `Y_it`: pasien mulai pengobatan;
- fixed effect provinsi;
- fixed effect bulan-tahun;
- standard error dikelompokkan pada provinsi;
- model terpisah untuk setiap eksposur sebagai hasil utama;
- model gabungan hanya sebagai sensitivitas karena korelasi antarvariabel iklim.

### 3. Lag dan nonlinieritas

- Utama: lag 0, 1, dan 2 bulan serta rerata lag 0-2.
- Hindari distributed lag nonlinear model yang sangat fleksibel pada 24 bulan; basis spline kompleks akan overfit.
- Nonlinieritas dibatasi pada indikator ekstrem dan, jika diperlukan, spline maksimal 2-3 derajat kebebasan yang dipraregistrasikan.

### 4. Modifikasi efek

Uji satu interaksi per model antara eksposur utama dan kerentanan yang telah dicenter:

- kemiskinan;
- sanitasi;
- kepadatan log.

Hasil interaksi dilaporkan sebagai eksploratif dan dikoreksi false discovery rate.

### 5. Outcome pengobatan

Gunakan model binomial berbobot denominator outcome-known pada cohort matang. Karena kematangan berkaitan dengan waktu follow-up, lakukan analisis 2024 sebagai utama dan cohort 2025 hanya bila snapshot baru menunjukkan pending share yang memadai.

### 6. Sensitivitas

- tambah jumlah kejadian hidrometeorologi BNPB;
- keluarkan provinsi yang memakai nearest POWER grid;
- winsorize count bencana, bukan outcome TB;
- negative binomial sebagai pembanding PPML;
- wild cluster bootstrap atau small-sample correction karena hanya 38 cluster;
- leave-one-province-out untuk memastikan hasil tidak digerakkan satu provinsi.

## Hasil eksplorasi awal

Model PPML awal dengan fixed effect provinsi dan bulan-tahun tidak menemukan asosiasi linear yang jelas antara anomali iklim dan jumlah pasien mulai pengobatan. IRR per +1 SD berada sangat dekat 1 dan interval kepercayaan mencakup 1. Hasil lengkap ada pada `results/preliminary_tb_climate_ppml_results.csv`.

Temuan nol ini **bukan kegagalan proyek**. Ini menunjukkan bahwa kontribusi ilmiah sebaiknya berpusat pada anomali ekstrem, heterogenitas kerentanan, lag yang dibatasi, dan transparansi data-maturity - bukan menjanjikan prediksi tinggi atau hubungan linear sederhana. Semua hasil awal bersifat eksploratif dan tidak boleh digunakan sebagai hipotesis konfirmatori tanpa preregistrasi terpisah.

## Risiko inferensi dan mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Hanya dua tahun | Seasonality dan tren sulit dipisahkan | fixed effect bulan-tahun; seasonality hanya deskriptif |
| Outcome 2025 provisional | success rate bias ke bawah | maturity flag; fokus count initiation; analisis outcome 2024 |
| Outcome bukan incidence | salah tafsir biologis | istilah wajib: treatment initiation/cohort, bukan incidence |
| BPS tahunan diulang per bulan | pseudo-variation | dipakai sebagai modifier/stratifier, bukan efek bulanan utama |
| Iklim reanalysis | measurement error spasial | area-grid BIG, flag nearest-grid, sensitivity exclusion |
| BNPB tidak reconcile | bias pelaporan | hanya sensitivitas; lampirkan reconciliation |
| 38 cluster | SE asimtotik kurang stabil | small-sample correction/wild cluster bootstrap |
| Banyak hipotesis | false positive | preregistrasi, outcome/lag primer tunggal, FDR sekunder |

## Kriteria kelayakan publikasi

Proyek layak dilanjutkan jika:

1. panel final tetap 912/912 tanpa missing wajib;
2. definisi SITB tidak diganti menjadi insidensi/notifikasi;
3. model primer dan satu lag utama dipraregistrasikan sebelum eksplorasi lanjutan;
4. bencana tetap berstatus sensitivitas;
5. dashboard memisahkan data resmi, turunan, dan provisional;
6. semua panel sintetis dikeluarkan dari tampilan produksi dan, jika perlu untuk demo, ditempatkan pada mode demo terpisah yang berlabel jelas.

## Rencana implementasi sistem

1. Tambahkan endpoint read-only untuk panel final dan metadata QA.
2. Jadikan `analysis_panel_tb_climate_disaster_2024_2025.csv` satu-satunya sumber panel riset provinsi-bulan.
3. Ganti panel sintetis dengan tiga tampilan: tren treatment initiation, anomali iklim, dan data maturity.
4. Tampilkan badge sumber dan tanggal snapshot pada setiap visual.
5. Nonaktifkan success-rate 2025 secara default bila pending share >5%.
6. Tambahkan halaman metodologi yang menampilkan codebook dan source ledger.

## Deliverable

- panel CSV siap analisis dan codebook;
- workbook audit/analisis;
- skrip ekstraksi yang reproducible;
- protokol statistik dan preregistration;
- dashboard data-real-only;
- manuscript dengan appendix provenance dan QA.

## Referensi ilmiah utama

Referensi berikut berasal dari jurnal yang lazim terindeks Scopus; status indeks perlu diverifikasi kembali melalui akses Scopus institusi pada saat submission karena cakupan indeks dapat berubah.

1. Kirolos A, et al. Tuberculosis case notifications in Malawi have strong seasonal and weather-related trends. *Scientific Reports*. 2021;11:4621. [DOI](https://doi.org/10.1038/s41598-021-84124-w). Relevan untuk weather lag, notifikasi, dan kehati-hatian interpretasi ekologis.
2. Gashu Z, et al. Seasonal patterns of tuberculosis case notification in the tropics of Africa: a six-year trend analysis in Ethiopia. *PLOS ONE*. 2018;13:e0207552. [DOI](https://doi.org/10.1371/journal.pone.0207552). Relevan untuk pola musim dan akses layanan.
3. Gasparrini A, Armstrong B, Kenward MG. Distributed lag non-linear models. *Statistics in Medicine*. 2010;29:2224-2234. [DOI](https://doi.org/10.1002/sim.3940). Referensi metodologis untuk lag, dengan catatan desain kita terlalu pendek untuk basis kompleks.
4. Association between averaged meteorological factors and tuberculosis risk: a systematic review and meta-analysis. *Environmental Research*. 2022. [Publisher page](https://www.sciencedirect.com/science/article/abs/pii/S0013935122006065). Dasar untuk pemilihan temperatur, kelembapan, dan hujan.
5. The impact of climate change on the risk factors for tuberculosis: a systematic review. *Environmental Research*. 2022. [DOI](https://doi.org/10.1016/j.envres.2022.113436). Dasar mekanisme melalui kemiskinan, overcrowding, malnutrisi, dan polusi udara.
6. Meteorological factors contribute to the risk of pulmonary tuberculosis: a multicenter study in eastern China. *Science of the Total Environment*. 2021. [Publisher page](https://www.sciencedirect.com/science/article/pii/S0048969721036937). Contoh efek nonlinear dan delayed.
7. Contributions of ambient temperature and relative humidity to the risk of tuberculosis admissions: a multicity study in Central China. *Science of the Total Environment*. 2022. [Publisher page](https://www.sciencedirect.com/science/article/pii/S0048969722033691). Contoh kerangka multicity dan pooling heterogenitas.

## Kesimpulan

Pendekatan terbaik sekarang adalah studi panel ekologis anomali iklim terhadap inisiasi pengobatan TB, dengan kerentanan BPS sebagai modifier dan BNPB sebagai sensitivitas. Data inti sudah benar-benar tersedia dan telah diekstrak. Keterbatasan dua tahun tidak dapat dihilangkan, tetapi dapat dikelola melalui pertanyaan yang tepat, model parsimonious, pembatasan klaim, dan audit provenance yang lengkap.

