# TB-INSIGHT: Data and Methods v0.8

> **Status:** Draft / working version — Revisi Climate & Spatial
> **Task:** `[S3-ADZ-01] Methods climate and spatial revision`
> **Deliverable path:** `docs/writing/manuscript-methods-v0.8.md`
> **Dependencies terpenuhi:** `[S3-VEN-02] Feature matrix QA` (Venedict; reviewer Dame) dan `[S3-DAM-01] Hotspot persistence analysis` (Dame Gabriela Silitonga)
> **Reviewer:** Dame
> **Perubahan dari v0.5:** Section 4 (Climate Exposures) dan Section 10 (Spatial Analysis) direvisi total dari *candidate/TBD* menjadi metodologi dan hasil aktual, berdasarkan `feature_matrix_qa.md` (OUT-QA-M1) dan `hotspot_S3-DAM-01.Rmd` beserta empat output CSV/JSON-nya. Study area disesuaikan ke cakupan 38 provinsi nasional.

---

## 1. Study Area and Study Design

### 1.1 Study Area

TB-INSIGHT mencakup **seluruh 38 provinsi Indonesia**, menggunakan `province_boundaries_38.geojson` sebagai batas administratif spasial.

### 1.2 Study Design

Studi ini adalah **ecological spatiotemporal analysis** dengan panel provinsi-bulan.

- **Periode studi:** Januari 2024 – Desember 2025 (24 periode bulanan), dikonfirmasi konsisten di seluruh 38 file profil provinsi, `analysis_panel_province_month_2024_2025.csv`, dan `climate_lags_v1.csv`.
- **Resolusi temporal:** Bulanan.
- **Cakupan data:** 24 bulan lengkap per provinsi, 0 periode hilang pada level provinsi-bulan (dikonfirmasi berulang di seluruh file profil: "24 Bulan Lengkap (0 Periode Hilang / Missing)").

**Status:** Confirmed.

### 1.3 Unit of Analysis

Unit analisis primer adalah **provinsi-bulan** (38 provinsi × 24 bulan = 912 observasi), konsisten dengan validasi `n_provinces_is_38: true` dan `n_months_is_24: true` pada `hotspot_persistence_validation_R.json`.

**Status:** Confirmed.

---

## 2. Data Sources

Berdasarkan `project_source_ledger.csv` (dirujuk di setiap file profil provinsi) dan `feature_matrix_qa.md`, integrasi data berasal dari:

| Domain | Sumber | Status |
| --- | --- | --- |
| TB outcome | SITB / Kemenkes RI | Confirmed |
| Populasi & sosioekonomi | BPS (`bps_province_annual_official.csv`) | Confirmed |
| Iklim | NASA POWER (historis 1981–2023, baseline klimatologi 1991–2020) | Confirmed |
| Bencana | BNPB | Terdaftar sebagai sumber (lihat catatan di Section 5.2 — peran variabelnya dalam model belum diklarifikasi) |
| Geografis | `province_boundaries_38.geojson` | Confirmed |
| Bobot spasial | `spatial_weights_v2_queen_bridge.csv` (dari S2-DAM-01) | Confirmed |

Dataset versi beku (*frozen*) yang digunakan: **Frozen Release v1** (`data/processed/release_v1/`), dikonfirmasi di seluruh file profil provinsi.

---

## 3. Outcome Variable

### 3.1 TB Treatment Initiation

Variabel yang digunakan dalam analisis spasial S3-DAM-01 adalah **`treatment_started_per_100k_population`** — rate bulanan pasien yang memulai pengobatan TB per 100.000 penduduk, per provinsi.

| Atribut | Definisi |
| --- | --- |
| Variabel | TB treatment initiation (rate per 100k) |
| Nama kolom panel | `treatment_started_per_100k_population` |
| Definisi | Jumlah pasien TB yang memulai pengobatan pada bulan tersebut, per 100.000 penduduk |
| Temporal resolution | Bulanan |
| Spatial resolution | Provinsi |
| Analytical role | Primary outcome (variabel LISA di S3-DAM-01) |
| Status missing | 0 (dikonfirmasi `no_na_in_monthly_variable: true` di validasi S3-DAM-01) |

### 3.2 Outcome Terminology (tidak berubah dari v0.5)

Outcome **wajib** disebut **"TB treatment initiation"**, bukan "TB incidence". Insidensi merujuk pada kasus baru dalam populasi; treatment initiation merujuk pada dimulainya pengobatan pada pasien yang teridentifikasi eligible. Aturan ini juga tercatat sebagai **Istilah Terlarang** di glossary manuskrip (`manuscript-outline-v1.md`): *"Insidensi (Incidence): DILARANG KERAS digunakan untuk merujuk pada data treatment initiation."*

### 3.3 Karakteristik Data Outcome yang Perlu Diperhatikan dalam Modeling

Ditemukan konsisten di seluruh 38 file profil provinsi, dua karakteristik struktural outcome yang relevan untuk Methods dan Limitations:

1. **Cohort maturity / pending share.** Setiap observasi provinsi-bulan memiliki `pending_share` — porsi kohort outcome pengobatan yang belum terisi (pasien masih dalam masa pengobatan). Bulan-bulan di akhir seri (terutama 2025 semester kedua) secara sistematis memiliki `pending_share` lebih tinggi ("Provisional", >5%) dibanding awal seri ("Matang"/Mature, ≤5%), karena kohort pengobatan berdurasi ~6 bulan belum tuntas saat data di-*freeze*. Ini **bukan data quality issue** melainkan karakteristik struktural sistem pelaporan SITB — namun berimplikasi pada keandalan observasi bulan-bulan terbaru dan perlu keputusan analitik eksplisit (lihat Section 17).
2. **Flag kualitas data per observasi:** `SITB_LIVE_REVISION_FLAG` dan `BNPB_OPERATIONAL_FLAG` muncul di hampir seluruh observasi (bukan penanda anomali spesifik, melainkan status standing pipeline), sementara flag lain — `HIGH_PENDING_2024`, `HIGH_PENDING_2025_LATE`, `MAD_OUTLIER`, `SHARP_MOM_JUMP` — menandai observasi individual yang perlu perhatian tambahan saat interpretasi (mis. `MAD_OUTLIER` pada Sumatera Utara 2025-10, Sumatera Selatan 2024-12 & 2025-10, Jawa Timur 2025-10, Kalimantan Selatan 2025-10, Bengkulu 2025-11, Papua Pegunungan 2025-10).

**Status:** Data karakteristik ini confirmed (dari data aktual); keputusan pemodelan atas keduanya (mis. apakah bulan "Provisional" di-*downweight*, dikeluarkan, atau dijadikan sensitivity check) masih **TBD** — lihat Section 17.

---

## 4. Climate Exposures — REVISI UTAMA

Section ini menggantikan total Section 4 v0.5 (yang berstatus *candidate/TBD*). Sumber: `feature_matrix_qa.md` (**OUT-QA-M1**), mengaudit deliverable **`data/processed/features/climate_lags_v1.csv`** (**OUT-DAT-M2**), dibuat oleh Venedict (S3-VEN-02), direview oleh Dame, status **LULUS pada seluruh 5 QA checkpoint**.

### 4.1 Variabel Iklim Terkonfirmasi

| Variabel | Definisi operasional | Unit | Resolusi temporal | Resolusi spasial | Status |
| --- | --- | --- | --- | --- | --- |
| Temperature | `temperature_c`; anomali z-score vs. baseline klimatologi 1991–2020 | °C | Bulanan | Provinsi | **Confirmed** |
| Relative humidity | `relative_humidity_pct`; anomali z-score vs. baseline 1991–2020 | % | Bulanan | Provinsi | **Confirmed** |
| Precipitation | `precipitation_mm`; anomali z-score vs. baseline 1991–2020 | mm | Bulanan | Provinsi | **Confirmed** |

Wind speed dan sunshine duration **tidak muncul** di `climate_lags_v1.csv` — tetap **Candidate/TBD**, tidak dikonfirmasi tersedia dalam pipeline saat ini.

### 4.2 Metode Agregasi dan Anomali (metode yang sebelumnya TBD di v0.5, kini confirmed)

- **Baseline klimatologi:** 1991–2020, dihitung dari data historis NASA POWER (1981–2023).
- **Skor anomali:** setiap observasi bulanan dikonversi menjadi z-score relatif terhadap baseline klimatologi tersebut (bukan nilai mentah langsung yang dipakai sebagai exposure).
- **Manfaat baseline historis:** karena baseline dihitung dari data 1981–2023 (bukan hanya dari window studi 2024–2025), fitur lag tidak kehilangan baris di awal panel (Januari 2024) — **0,00% missing** pada seluruh 33.744 sel (912 baris × 37 kolom).

### 4.3 Struktur Lag (menjawab TBD "Exposure Lag Structure" di v0.5 Section 9)

| Item | Spesifikasi |
| --- | --- |
| Exposure yang di-lag | Temperature, relative humidity, precipitation (semua dalam skor-z anomali) |
| Lag yang disediakan | `lag0` (bulan berjalan), `lag1`, `lag2`, `lag3` (1–3 bulan sebelumnya) |
| Unit lag | Bulan |
| Jenis lag | Individual per-lag tersedia; **belum ada** kolom cumulative lag eksplisit — `mean_lag0_2` tersedia sebagai rata-rata 3 bulan (lag0–lag2) |
| Metode estimasi asosiasi lag | Belum ditentukan (menunggu spesifikasi model statistik final, Section 11) |

**Audit lag alignment:** Diverifikasi presisi 100% pada sampel 5 provinsi (Jambi, DI Yogyakarta, Maluku, Papua Barat Daya, Papua Tengah) pada periode target 2024-04: `lag1(t) == z(t−1)`, `lag2(t) == z(t−2)`, `lag3(t) == z(t−3)` cocok tepat di seluruh sampel. Batas transisi tahun (Januari 2024, lag ditarik dari Oktober–Desember 2023 memakai data historis NASA POWER) juga diverifikasi tidak mengalami *future data leakage* maupun kehilangan baris.

### 4.4 Audit Rentang Nilai dan Autokorelasi

- **Tidak ada outlier ekstrem** (|z| > 5) di seluruh kolom z-score. Nilai maksimum yang tercatat: z-temperature lag3 = +4,74; z-temperature lag0 = +4,19 (diduga terkait gelombang panas 2024 di Sumatra/Jawa — dicatat sebagai kejadian riil, bukan corruption data).
- **Pola peluruhan autokorelasi (autocorrelation decay)** konsisten dan wajar di ketiga variabel (tidak ada pembalikan seperti lag3 > lag1):
  - Temperature: lag0↔lag1 = 0,756 → lag0↔lag2 = 0,688 → lag0↔lag3 = 0,528
  - Relative humidity: lag0↔lag1 = 0,486 → lag0↔lag2 = 0,371 → lag0↔lag3 = 0,177
  - Precipitation: lag0↔lag1 = 0,198 → lag0↔lag2 = 0,202 → lag0↔lag3 = 0,106 (memori temporal curah hujan lebih pendek dibanding suhu — konsisten karakteristik iklim tropis)

### 4.5 Status Ringkas vs. v0.5

| Item TBD di v0.5 | Status di v0.8 |
| --- | --- |
| Exact climate variables included | **Resolved** — temperature, RH, precipitation |
| Climate aggregation method | **Resolved** — anomali z-score vs. baseline klimatologi 1991–2020 |
| Spatial resolution of climate data | **Resolved** — provinsi |
| Exposure lag structure | **Resolved (struktur)** — lag0–lag3 bulanan + mean_lag0_2; metode estimasi asosiasi lag masih TBD (Section 11) |

---

## 5. Social, Demographic, and Health-System Covariates

### 5.1 Variabel Sosioekonomi Terkonfirmasi (dari `feature_matrix_qa.md` Checkpoint 5)

| Variabel | Kolom panel | Sumber & periode referensi asli | Granularitas | Status |
| --- | --- | --- | --- | --- |
| Akses sanitasi layak | `sanitation_access_pct` | BPS Susenas, ref. `"2024 (Susenas)"` | Tahunan, direplikasi konstan per bulan | **Confirmed** |
| Kemiskinan | `poverty_pct` | BPS Susenas, ref. `"Maret 2024 (Susenas)"` | Tahunan, direplikasi konstan per bulan | **Confirmed** |
| Populasi & kepadatan | `population` | BPS, ref. tanggal `"2024-06-30"` | Tahunan (titik waktu), direplikasi konstan per bulan | **Confirmed** |

Healthcare access, healthcare preparedness, Human Development Index/MHDI, treatment coverage, dan treatment success rate **tidak muncul** di feature matrix yang diaudit — tetap **Candidate/TBD**.

### 5.2 Catatan Metodologis Penting untuk Spesifikasi Model

Ketiga variabel BPS di atas **tidak memiliki variasi intra-tahunan** (1 nilai unik per provinsi per tahun, direplikasi identik Januari–Desember). Implikasi untuk PPML dengan *Province Fixed Effects* (lihat Section 11): efek variabel sosial tahunan ini **akan diserap oleh province fixed effect dan/atau year fixed effect**, sehingga koefisiennya tidak dapat diestimasi secara terpisah dalam spesifikasi FE penuh — ini perlu dinyatakan eksplisit di bagian model spesifikasi manuskrip final, bukan disembunyikan.

Variabel **BNPB (bencana)** terdaftar sebagai sumber data (Section 2) dan muncul sebagai flag standing (`BNPB_OPERATIONAL_FLAG`) di hampir seluruh observasi panel outcome, namun **belum ada kolom bencana kuantitatif yang teraudit** di `climate_lags_v1.csv`. Perannya sebagai exposure/covariate belum jelas — **TBD**, butuh klarifikasi dari tim data (lihat Section 17).

---

## 6. Environmental and Air-Pollution Exposures

Tidak berubah dari v0.5 — **tidak ada bukti** SO₂/NO₂/PM₁₀/PM₂.₅/CO/O₃ tersedia di pipeline manapun yang diaudit sejauh ini (baik `feature_matrix_qa.md` maupun file profil provinsi). Tetap **Candidate/TBD**, hanya didukung oleh literatur, bukan data proyek.

---

## 7. Geographic and Spatial Data

| Variabel | Definisi | Sumber | Status |
| --- | --- | --- | --- |
| Provinsi | 38 unit administratif | `province_boundaries_38.geojson` | **Confirmed** |
| Administrative boundary | Poligon batas 38 provinsi | `province_boundaries_38.geojson` | **Confirmed** |
| Spatial weights (primer) | Queen contiguity + koreksi *bridge* v2 | `spatial_weights_v2_queen_bridge.csv` (dari S2-DAM-01) | **Confirmed** |
| Coordinate reference system | — | — | **TBD** |

**Validasi struktur bobot spasial** (dari `hotspot_persistence_validation_R.json`): 0 provinsi tanpa tetangga (`no_island_in_primary: true`), dan seluruh 38 provinsi membentuk **1 connected component** (`primary_has_1_connected_component: true`) — artinya graf ketetanggaan tidak terpecah menjadi sub-graf terisolasi, prasyarat penting bagi validitas uji permutasi spasial global maupun lokal.

---

## 8. Temporal Variables

| Variabel | Definisi | Status |
| --- | --- | --- |
| Year | 2024, 2025 | **Confirmed** |
| Month | 1–12 | **Confirmed** |
| Period | `YYYY-MM`, 24 level unik | **Confirmed** |

---

## 9. Exposure Lag Structure

Digantikan oleh Section 4.3 di atas (struktur lag iklim sekarang confirmed). Lag untuk variabel non-iklim (sosial, bencana) **belum relevan** karena variabel tersebut tahunan/statis (Section 5.2) atau belum teraudit (bencana).

---

## 10. Spatial Analysis — REVISI UTAMA

Section ini menggantikan total Section 10 v0.5. Sumber: `hotspot_S3-DAM-01.Rmd` (Dame Gabriela Silitonga), empat output CSV, dan `hotspot_persistence_validation_R.json` (**OUT-VAL-M1**). Status task di ClickUp: **In Progress** — hasil di bawah adalah hasil aktual dari run yang tersimpan namun deliverable belum ditandai selesai; manuskrip mengutip sebagai hasil sementara yang perlu dikonfirmasi ulang saat task ditutup.

### 10.1 Metode: Local Indicators of Spatial Association (LISA) Bulanan

| Parameter | Spesifikasi | Sumber |
| --- | --- | --- |
| Metode | Local Moran's I via `localmoran_perm` (conditional permutation LISA) | `spdep` (R) |
| Variabel | `treatment_started_per_100k_population` | Panel provinsi-bulan |
| Bobot spasial | `spatial_weights_v2_queen_bridge.csv`, style `"W"` (row-standardized), Queen + bridge v2 | S2-DAM-01 |
| Unit cross-section | 38 provinsi, dijalankan **terpisah untuk tiap 24 bulan** | — |
| Jumlah permutasi | 999 | Pre-specified |
| Seed reproducibility | 20260902 (`iseed`, identik untuk seluruh 24 bulan) | Pre-specified |
| Alpha | 0,05 | Pre-specified |
| Kolom p-value | Dipilih eksplisit dengan prioritas `"Pr(folded) Sim"` lalu `"Pr(z != E(Ii)) Sim"` (bukan tebakan/default library) | — |
| Koreksi multiple testing | **Benjamini-Hochberg (FDR)**, dihitung **per bulan** lintas 38 provinsi | Konsisten dengan pendekatan S2-DAM-02 |
| Ambang signifikansi final | **`p_fdr < 0,05`** (bukan p mentah) | Pre-specified |
| Klasifikasi kuadran | High-High, Low-Low, High-Low, Low-High — berdasarkan tanda z-score nilai dan z-score spatial lag (`lag.listw`) | — |

### 10.2 Definisi Persistence (Pre-Specified Sebelum Melihat Hasil)

Untuk setiap provinsi: `n_HH` = jumlah bulan (dari 24) signifikan FDR **dan** High-High; `n_LL` = jumlah bulan signifikan FDR **dan** Low-Low. Enam kategori saling eksklusif:

| Kategori | Syarat |
| --- | --- |
| Persistent Hotspot | `n_HH ≥ 12` |
| Persistent Coldspot | `n_LL ≥ 12` |
| Sporadic Hotspot | `0 < n_HH < 12` dan `n_LL = 0` |
| Sporadic Coldspot | `0 < n_LL < 12` dan `n_HH = 0` |
| Mixed/Unstable | `n_HH > 0` **dan** `n_LL > 0` |
| Not significant | `n_HH = 0` dan `n_LL = 0` |

Ambang 12/24 (50% dari periode studi) dipilih sebagai titik tengah paling netral, **ditetapkan sebelum menjalankan analisis** — bukan hasil *post-hoc* setelah melihat distribusi. Seluruh 6 kategori ditampilkan di legenda peta dan tabel, termasuk kategori dengan anggota nol — acceptance criteria S3-DAM-01 secara eksplisit melarang menyembunyikan observasi non-signifikan/tidak cukup data.

### 10.3 Hasil — Versi FDR-Corrected (Primer)

**Seluruh 38 provinsi jatuh ke kategori "Not significant"** (**OUT-TBL-M1** → `hotspot_persistence_R.csv`). Tidak ada satu pun dari 912 observasi provinsi-bulan yang mencapai `p_fdr < 0,05` (**OUT-DAT-M1** → `hotspot_monthly_lisa_R.csv`; nilai `p_fdr` minimum yang teramati ≈ 0,089, di atas ambang 0,05 namun tidak jauh). Konsekuensinya, jumlah transisi label antarbulan = 0 untuk seluruh provinsi (**OUT-TBL-M3** → `hotspot_stability_transitions_R.csv`) — label tetap "Insignificant" sepanjang 24 bulan secara trivial.

> Sesuai catatan pre-specified di `hotspot_S3-DAM-01.Rmd` Section 14: hasil "seluruhnya abu-abu" ini **secara eksplisit ditampilkan sebagai temuan jujur**, bukan disembunyikan — konsisten dengan hasil S2-DAM-02 yang juga menunjukkan sedikit signifikansi setelah koreksi FDR pada cross-section rata-rata 24 bulan. Ini kemungkinan mencerminkan **keterbatasan daya statistik (statistical power)** untuk uji lokal pada 38 unit spasial dengan koreksi multiple-testing yang ketat, bukan ketiadaan pola spasial sama sekali (lihat versi eksploratif di 10.4).

### 10.4 Hasil — Versi Eksploratif, p Mentah (Tanpa Koreksi FDR)

Sebagai pembanding eksploratif — **bukan pengganti** hasil 10.3 — versi yang sama dihitung ulang memakai ambang p mentah < 0,05 tanpa koreksi multiple testing (**OUT-TBL-M2** → `hotspot_persistence_raw_R.csv`):

| Provinsi | n_HH (raw) | n_LL (raw) | Kategori (raw, eksploratif) |
| --- | --- | --- | --- |
| Papua Tengah | 24 | 0 | Persistent Hotspot |
| Nusa Tenggara Barat | 0 | 24 | Persistent Coldspot |
| Sumatera Selatan | 0 | 20 | Persistent Coldspot |
| Jawa Timur | 0 | 15 | Persistent Coldspot |
| Jawa Barat | 3 | 0 | Sporadic Hotspot |
| DKI Jakarta | 2 | 0 | Sporadic Hotspot |
| Banten | 1 | 0 | Sporadic Hotspot |
| 31 provinsi lain | 0 | 0 | Not significant |

Papua Tengah signifikan High-High secara raw di **seluruh 24 dari 24 bulan** — pola paling konsisten di seluruh dataset, namun tidak bertahan setelah koreksi FDR bulanan lintas 38 provinsi. Pola ini **tidak boleh dikutip sebagai klaim final** di narasi hasil; fungsinya murni menunjukkan "ada apa di balik" hasil FDR sebelum koreksi diterapkan, sesuai catatan eksplisit di Rmd.

### 10.5 Validasi Reproducibility

Seluruh 7 pemeriksaan validasi pada `hotspot_persistence_validation_R.json` (**OUT-VAL-M1**) **PASS**, tanpa `failed_checks`: jumlah provinsi = 38, jumlah bulan = 24, tidak ada NA pada variabel outcome bulanan, tidak ada provinsi terisolasi pada bobot spasial primer, bobot spasial primer membentuk 1 connected component, seluruh provinsi memiliki kategori persistence, dan keenam kategori legenda tercatat lengkap.

### 10.6 Status Ringkas vs. v0.5

| Item TBD di v0.5 Section 10 | Status di v0.8 |
| --- | --- |
| Global Moran's I | Belum dijalankan terpisah di S3-DAM-01 (yang dijalankan adalah Local Moran's I / LISA per bulan) — tetap **TBD** untuk versi global |
| Local Moran's I | **Resolved** — dijalankan bulanan, 999 permutasi, FDR per bulan |
| Getis-Ord Gi* | **TBD**, tidak dijalankan di S3-DAM-01 |
| GWR, CAR/BYM, Bayesian spatiotemporal | **TBD**, belum dijalankan |
| Metode klasifikasi persistence antarbulan | **Resolved** — skema 6 kategori, ambang 12/24, pre-specified |

---

## 11. Statistical Analysis and Model

### 11.1 Arah Model yang Kini Confirmed sebagai Prioritas

`feature_matrix_qa.md` mencatat secara eksplisit bahwa `climate_lags_v1.csv` disiapkan untuk **PPML (Poisson Pseudo-Maximum-Likelihood) modeling oleh Stephen di Sprint 4**, dengan **Province Fixed Effects** sebagai struktur yang diasumsikan menyerap variasi tahunan variabel sosial BPS (Section 5.2).

| Komponen | Status |
| --- | --- |
| Outcome distribution | PPML (arah confirmed sebagai prioritas Sprint 4) — pilihan akhir vs. Negative Binomial masih **TBD** menunggu penilaian dispersi data aktual |
| Fixed effects | Province Fixed Effects disebutkan eksplisit; Year Fixed Effect disebut sebagai kemungkinan tambahan — **TBD** final |
| Exposure variables | Kandidat kuat: temperature, RH, precipitation (anomali z-score, lag0–lag3) — Section 4 |
| Covariates | Sanitation access, poverty, population (BPS tahunan) — akan sebagian diserap FE, lihat 5.2 |
| Spatial effects | Belum diintegrasikan ke model statistik utama — S3-DAM-01 sejauh ini analisis deskriptif-eksploratif spasial (LISA), bukan spatial regression/CAR/BYM dalam model outcome. **TBD** |
| Lag structure dalam model | Struktur data tersedia (lag0–lag3); metode estimasi asosiasi (mis. distributed lag, single-lag terpilih, atau cumulative) — **TBD** |
| Model selection & evaluation criteria | **TBD** |

Ini tetap merupakan pertimbangan metodologis, **bukan spesifikasi final** — Sprint 4 (modeling) berada di luar cakupan task ini.

---

## 12. Data Integration and Spatial-Temporal Linkage

Tidak berubah secara struktural dari v0.5, namun kini confirmed berjalan sebagaimana dirancang:

- **Spatial identifier:** provinsi (kode BPS, mis. `11` = Aceh, `35` = Jawa Timur, dst. — dikonfirmasi di seluruh file profil provinsi).
- **Temporal identifier:** `period` (`YYYY-MM`).
- **Spatial boundaries:** `province_boundaries_38.geojson`.
- **Linkage climate → panel:** dikonfirmasi 0% missing dan 100% lag alignment tepat (Section 4.3).
- **Linkage sosial (BPS tahunan) → panel bulanan:** replikasi konstan per tahun kalender, dikonfirmasi (Section 5.1–5.2).

---

## 13. Ethics and Data Limitations

### 13.1 Data Ethics

Tidak berubah dari v0.5 — status persetujuan etik/exemption masih **TBD**.

### 13.2 Keterbatasan Data (diperbarui dengan temuan aktual)

Selain daftar keterbatasan generik di v0.5, ditambahkan keterbatasan yang **sudah terverifikasi secara langsung** dari data dan hasil aktual:

- **Cohort maturity / pending share** meningkat tajam menjelang akhir seri data (hingga >40–60% di beberapa provinsi pada 2025-12, mis. Papua Pegunungan, Kalimantan Selatan) — observasi bulan-bulan terakhir seri berisiko under-count sistematis dan perlu penanganan eksplisit dalam model (Section 3.3, item terbuka di Section 17).
- **Daya statistik terbatas untuk LISA pada 38 unit spasial**: seluruh 912 observasi provinsi-bulan tidak mencapai signifikansi setelah koreksi FDR bulanan (Section 10.3) — dicatat sebagai keterbatasan daya uji, bukan bukti ketiadaan pola spasial (versi eksploratif p mentah di Section 10.4 menunjukkan pola yang masih layak didokumentasikan, tapi tidak untuk diklaim).
- **Variabel bencana (BNPB) belum terintegrasi secara kuantitatif** ke feature matrix yang teraudit — perannya belum jelas.
- Kesimpulan spasial pada Section 10 mencerminkan pola **dalam rentang 24 bulan yang tersedia saja**, bukan klaim persistence jangka panjang.

---

## 14. Variable Role Summary

| Variable group | Candidate/confirmed variables | Status | Intended analytical role |
| --- | --- | --- | --- |
| Outcome | TB treatment initiation (`treatment_started_per_100k_population`) | **Confirmed** | Primary outcome |
| Climate | Temperature, relative humidity, precipitation (z-score anomali, lag0–lag3) | **Confirmed** | Primary exposures |
| Additional climate | Wind speed, sunshine duration | Candidate/TBD | — |
| Social | Poverty, sanitation access, population (BPS tahunan) | **Confirmed** (tersedia); peran dalam model FE — TBD | Covariate (sebagian diserap FE) |
| Healthcare | Healthcare access, healthcare preparedness | Candidate/TBD | — |
| Disaster | BNPB (bencana) | Sumber terdaftar; kolom kuantitatif belum teraudit | TBD |
| Environmental | SO₂, NO₂, PM₂.₅, PM₁₀, CO, O₃ | Candidate/TBD (literatur saja) | — |
| Spatial | Provinsi, batas administratif, bobot Queen+bridge v2 | **Confirmed** | Spatial identifiers & weights |
| Spatial analysis | LISA bulanan + klasifikasi persistence 6 kategori | **Confirmed (metode & hasil sementara)** | Deskriptif-eksploratif spasial |
| Temporal | Month, year, period | **Confirmed** | Temporal identifiers |

---

## 15. Methodological Evidence from Previous Studies

Tidak berubah dari v0.5 (Chen et al. 2023; Chang et al. 2024; Septiono et al. 2026; Tosepu et al. 2024; Shaweno et al. 2018; Farkhan et al. 2026; Mohidem et al. 2021; Sun et al. 2015; Liyew et al. 2024) — lihat v0.5 Section 15 dan References (Section 16) untuk detail lengkap serta DOI. Referensi ini tetap mendukung pemilihan variabel dan opsi metodologis, tidak menggantikan spesifikasi TB-INSIGHT aktual di atas.

---

## 16. Output ID Legend (Baru di v0.8)

Mengikuti konvensi project: Output ID dipetakan langsung ke nama file sumber, untuk traceability.

| Output ID | File sumber | Isi |
| --- | --- | --- |
| OUT-QA-M1 | `results/qa/feature_matrix_qa.md` | Laporan QA feature matrix iklim (5 checkpoint, LULUS) |
| OUT-DAT-M2 | `data/processed/features/climate_lags_v1.csv` | Feature matrix iklim: raw, anomali z-score, lag0–lag3, mean_lag0_2 |
| OUT-DAT-M1 | `hotspot_monthly_lisa_R.csv` | Hasil LISA bulanan mentah (912 baris: 38 provinsi × 24 bulan) |
| OUT-TBL-M1 | `hotspot_persistence_R.csv` | Klasifikasi persistence per provinsi (FDR-corrected, primer) |
| OUT-TBL-M2 | `hotspot_persistence_raw_R.csv` | Klasifikasi persistence per provinsi (p mentah, eksploratif) |
| OUT-TBL-M3 | `hotspot_stability_transitions_R.csv` | Jumlah transisi label FDR antarbulan per provinsi |
| OUT-VAL-M1 | `hotspot_persistence_validation_R.json` | Manifest validasi reproducibility S3-DAM-01 (7 checks, status PASS) |

---

## 17. Items Requiring Confirmation Before v1.0

Item yang **sudah resolved** di v0.8 dicoret secara konseptual (dipindah ke badan teks di atas dengan status Confirmed) dan tidak diulang di sini. Item yang tersisa:

- [ ] Exact TB treatment initiation numerator/denominator (definisi eligible patient) dari SITB.
- [ ] Keputusan penanganan bulan "Provisional" (`pending_share` >5%, terutama akhir 2025) dalam model — di-downweight, dikeluarkan, atau sensitivity check terpisah?
- [ ] Klarifikasi peran variabel BNPB/bencana — apakah akan menjadi exposure kuantitatif, atau sekadar metadata sumber?
- [ ] Status task `[S3-DAM-01]` di ClickUp masih "In Progress" — hasil Section 10 perlu dikonfirmasi ulang saat task tersebut resmi selesai/direview.
- [ ] Healthcare access, healthcare preparedness, HDI/MHDI, treatment coverage, treatment success rate — ketersediaan datanya di pipeline belum terkonfirmasi.
- [ ] Variabel lingkungan/polusi udara (SO₂, NO₂, PM₁₀, PM₂.₅, CO, O₃) — tidak ada bukti data tersedia; perlu diputuskan apakah tetap dicantumkan sebagai limitation atau dihapus dari manuskrip.
- [ ] Coordinate reference system untuk `province_boundaries_38.geojson`.
- [ ] Spesifikasi final model PPML: link function, daftar lengkap covariate, interaction terms, metode estimasi lag (single vs. distributed vs. cumulative), model selection/evaluation criteria (Sprint 4, di luar cakupan task ini).
- [ ] Apakah metode spasial tambahan (Global Moran's I, Getis-Ord Gi*, GWR, CAR/BYM, Bayesian spatiotemporal) akan dijalankan, atau LISA persistence dianggap cukup untuk manuskrip ini.
- [ ] Sensitivity check ambang persistence alternatif (mis. 8/24) — didiskusikan di Rmd sebagai keputusan metodologis terpisah, belum dijalankan.
- [ ] Status ethics approval/exemption.

> **Version-control note:** Dokumen ini v0.8. Section 4 dan 10 sudah berpindah dari *candidate/TBD* menjadi metodologi dan hasil aktual (dengan hasil Section 10 masih berstatus sementara mengikuti status task ClickUp). Section lain yang masih TBD harus tetap ditandai sebagai TBD, bukan diasumsikan, sampai dikonfirmasi dari dataset final dan analysis plan.