# TB-INSIGHT: Results Shell & Novelty Claim Audit v0.5

> **Task:** `[S3-ADZ-02] Results shell dan novelty claim audit`
> **Deliverable path:** `docs/writing/results-shell-v0.5.md`
> **Dependencies:** `[S3-STE-02]` (sebagian tersedia — Task 3/5/6; forecasting & ILP belum), `[S3-ADZ-01]` (tersedia — `manuscript-methods-v0.8.md`)
> **Acceptance criteria:** Setiap klaim memiliki output ID dan referensi; novelty tidak dinyatakan absolut tanpa bukti.

---

## 0. Status Dependency

`[S3-STE-02]` — hasil modeling PPML sudah diterima **sebagian**: Task 3 (baseline/primary model), Task 5 (lag sensitivity), dan Task 6 (social interaction) sudah tersedia dan mengisi RQ1 (Section 1.1). Model forecasting time-series (untuk RQ3) dan model optimisasi ILP (RQ4) **belum** diterima — Section 1.3 dan 1.4 tetap shell kosong.

Dua sumber tambahan diaudit untuk pembuatan dokumen ini yang belum pernah dirujuk di deliverable sebelumnya:

- **`TBINSIGHT_LongTerm_IRIS_Project_Final_Draft.pdf`** (**OUT-SRC-PITCH**) — dek proposal/rekrutmen proyek asli, 15 halaman, berskala **Kota Surabaya, 31 kecamatan**, bergantung pada akses data Dinkes. Ini adalah sumber sebagian besar klaim novelty yang diaudit di Section 3.
- **`TBINSIGHTliteratureevidencematrix.xlsx`** (**OUT-EVID**) — matriks evidence 10 studi literatur (Chen 2023, Chang 2024, Tedijanto 2018, Shaweno 2018, Farkhan 2026, Septiono 2026, Tosepu 2024, Liyew 2024, Mohidem 2021, Sun 2015), sama dengan yang dirujuk di `manuscript-methods-v0.5.md`/`v0.8.md`.

---

## 1. Results — Shell per RQ (mengikuti struktur `manuscript-outline-v1.md`)

### 1.1 RQ1 — Determinant Factors of TB

**Status: Terisi — hasil aktual dari `[S3-STE-02]` Task 3 (baseline), Task 5 (lag sensitivity), Task 6 (interaction) tersedia.** Ketiganya satu keluarga spesifikasi PPML yang sama: Poisson GLM (log link), outcome `jumlah_pasien`, offset `log_population_offset`, fixed effects province + period, SE cluster-robust per provinsi.

#### 1.1.1 Model Primer (Task 3, revised) — Main Effect Iklim

Struktur direvisi dari rencana awal (satu model joint) menjadi **3 model primary single-exposure** (satu variabel iklim per model, lag0–2 mean) plus **1 model joint sebagai sensitivity** untuk mengecek multikolinearitas (**OUT-MDL-T3-META**).

| Model | Exposure | IRR | 95% CI | p | Output ID |
| --- | --- | --- | --- | --- | --- |
| Primary — Temperature | `temperature_c_z_mean_lag0_2` | 0,997 | [0,982–1,012] | 0,669 | OUT-MDL-T3-TEMP |
| Primary — Precipitation | `precipitation_mm_z_mean_lag0_2` | 1,004 | [0,993–1,016] | 0,453 | OUT-MDL-T3-PRECIP |
| Primary — Humidity | `relative_humidity_pct_z_mean_lag0_2` | 1,003 | [0,987–1,019] | 0,705 | OUT-MDL-T3-HUM |
| Sensitivity — Joint (ketiganya bareng) | ketiga variabel di atas | 0,997 / 1,004 / 1,000 | — | 0,720 / 0,475 / 1,000 | OUT-MDL-T3-JOINT |

**Temuan utama:** tidak ada satu pun exposure iklim (main effect, lag0–2 mean) yang signifikan secara statistik — baik sendiri-sendiri (model primary) maupun disesuaikan bersama di model joint (**OUT-MDL-T3-ALL** → `coefficients_all_models.csv`). Ini harus dilaporkan apa adanya sebagai **null finding**, bukan disembunyikan.

#### 1.1.2 Sensitivity — Lag Individual (Task 5)

9 model tambahan (3 keluarga iklim × lag0/lag1/lag2 individual, single-family) sebagai sensitivity terhadap Task 3 (**OUT-MDL-T5-ALL** → `coefficients_all_lags.csv`). Hanya **precipitation lag1** yang nominal signifikan (IRR 1,006, 95% CI [1,001–1,011], p=0,027) — efek kecil, dan `selection_rule.md` (**OUT-MDL-T5-RULE**) melarang eksplisit mempromosikan satu lag jadi "hasil utama" hanya karena p-nya paling kecil di antara 9 model. Lag3 dan lag0–3 mean tidak dijalankan karena variabelnya tidak ada di panel beku, didokumentasikan (bukan disembunyikan) di **OUT-MDL-T5-SKIP** → `skipped_models.csv`.

#### 1.1.3 Effect Modification — Interaksi Iklim × Kerentanan Sosial (Task 6)

9 model interaksi (3 iklim × 3 penanda kerentanan: poverty, population density, sanitation access), satu interaksi per model (**OUT-MDL-T6-ALL** → `coefficients_all_interactions.csv`):

| Interaksi | IRR interaksi | 95% CI | p | Catatan |
| --- | --- | --- | --- | --- |
| humidity × sanitation | 0,974 | [0,966–0,983] | 2,2×10⁻⁹ | *** |
| precipitation × sanitation | 0,984 | [0,976–0,992] | 8,3×10⁻⁵ | *** |
| temperature × density | 1,005 | [1,002–1,008] | 0,0020 | ** — lihat catatan leverage Jakarta di bawah |
| precipitation × poverty | 0,988 | [0,980–0,997] | 0,0064 | ⚠️ jangan dilaporkan — lihat isu data |
| humidity × density | 0,997 | [0,994–0,999] | 0,012 | * — lihat catatan leverage Jakarta di bawah |
| temperature × sanitation | 1,016 | [1,003–1,029] | 0,015 | * |
| temperature × poverty | 1,023 | [0,987–1,059] | 0,21 | ⚠️ jangan dilaporkan — lihat isu data |
| humidity × poverty | 0,990 | [0,978–1,003] | 0,12 | ⚠️ jangan dilaporkan — lihat isu data |
| precipitation × density | 0,998 | [0,994–1,002] | 0,34 | |

**Tiga isu data yang wajib disertakan bila hasil ini dikutip (OUT-MDL-T6-ISSUE → `issue_log.md`):**
- **T6-01 (HIGH):** `poverty_pct` berisi nilai implausible (>100%, hingga 25.899% di Papua Pegunungan) pada 60/912 observasi (5 provinsi: DKI Jakarta, Papua Barat Daya, Papua Selatan, Papua Tengah, Papua Pegunungan) — diduga salah unit di sumber data. Standardisasi jadi rusak (SD≈2951, bukan ~3–5). **Ketiga model `*_x_poverty` tidak boleh diinterpretasikan/dilaporkan** sampai `poverty_pct` diperbaiki dan model di-rerun.
- **T6-02 (LOW/INFO):** `population_density_per_km2` sangat right-skewed (DKI Jakarta = 16.165/km², provinsi Papua serendah 5/km²) — valid secara riil, tapi menjadikan observasi Jakarta sebagai leverage point berpengaruh pada kedua model `*_x_density` yang signifikan di atas. Disarankan log-transform sebagai amandemen eksploratif terpisah, bukan mengubah hasil primer yang sudah ada.
- **T6-03 (INFO):** Ketiga penanda kerentanan bersifat time-invariant dalam panel (nilai BPS tahunan per provinsi) sehingga main effect-nya diserap province FE; interaction term tetap teridentifikasi dari variasi within-province pada exposure iklim, tapi ini membatasi interpretasi kausal (tidak bisa dibedakan apakah kerentanan memoderasi jalur biologis atau respons sistem kesehatan).
- 9 p-value **tidak** di-adjust multiple testing (**OUT-MDL-T6-MULT** → `multiplicity_note.md`) — signifikansi nominal harus diperlakukan eksploratif.

#### 1.1.4 Narasi Terpadu RQ1

Main effect iklim (Task 3) null secara konsisten di seluruh spesifikasi (single-family, joint, dan hampir seluruh lag individual di Task 5). Namun beberapa interaksi iklim × kerentanan sosial (Task 6) signifikan setelah province+period FE — menunjukkan asosiasi iklim-TB kemungkinan **bersyarat (conditional) pada kerentanan sosial wilayah**, bukan efek langsung yang seragam. Ini narasi yang jujur dan didukung data, **bukan** klaim "variabel prediktor dominan teridentifikasi" seperti disebut di outline RQ1 asli — karena yang ditemukan justru ketiadaan main effect, dengan interaksi terbatas sebagai temuan sekunder eksploratif.

| Sub-klaim outline asli | Status vs. bukti aktual |
| --- | --- |
| "Variabel prediktor dominan TB teridentifikasi" | **Tidak didukung sebagaimana diframing** — main effect iklim seluruhnya null; klaim RQ1 perlu ditulis ulang sebagai "tidak ada main effect iklim yang signifikan; interaksi dengan kerentanan sosial ditemukan terbatas dan eksploratif" |
| "Nilai signifikansi per variabel" | Tersedia lengkap (Section 1.1.1–1.1.3), termasuk yang non-signifikan — tidak disembunyikan |

### 1.2 RQ2 — Spatiotemporal Risk Map / Klasterisasi Spasial

**Status: Terisi sebagian — hasil aktual dari `[S3-DAM-01]` tersedia, tapi hasilnya adalah temuan null, bukan risk map yang tervalidasi.**

Analisis LISA bulanan (Local Moran's I, 999 permutasi, FDR Benjamini-Hochberg per bulan lintas 38 provinsi — lihat `manuscript-methods-v0.8.md` Section 10 untuk metodologi lengkap) menghasilkan:

- **Seluruh 38 provinsi berkategori "Not significant"** setelah koreksi FDR di sepanjang 24 bulan (**OUT-TBL-M1** → `hotspot_persistence_R.csv`); tidak ada satu pun dari 912 observasi provinsi-bulan mencapai `p_fdr < 0,05` (**OUT-DAT-M1**).
- Versi eksploratif p-mentah (tanpa koreksi) menunjukkan Papua Tengah sebagai raw persistent hotspot (24/24 bulan) dan tiga provinsi (Nusa Tenggara Barat, Sumatera Selatan, Jawa Timur) sebagai raw persistent coldspot (**OUT-TBL-M2**) — eksploratif, tidak untuk diklaim final.
- Validasi reproducibility PASS penuh (**OUT-VAL-M1**).

**Catatan penting untuk narasi Results:** hasil ini **tidak** bisa disajikan sebagai "TB Risk Map" dalam pengertian pitch/outline asli (peta klasifikasi High/Medium/Low Risk per unit, tervalidasi terhadap ground truth). Yang tersedia adalah hasil deskriptif-eksploratif LISA yang secara statistik sebagian besar null. Lihat audit novelty Section 3, klaim #2.

### 1.3 RQ3 — Forecasting Performance

**Status: PENDING — blocked pada `[S3-STE-02]`.**

| Sub-klaim | Output ID (placeholder) | Status |
| --- | --- | --- |
| Perbandingan performa model (ARIMA vs XGBoost vs RF, atau PPML — lihat audit #4) | `OUT-TBL-RQ3` *(belum ada)* | PENDING |
| Visualisasi confidence band prediksi 3 bulan | `OUT-FIG-RQ3` *(belum ada)* | PENDING |

### 1.4 RQ4 — Screening Allocation Strategy (ILP)

**Status: PENDING — tidak ada task/output ILP yang pernah diberikan di sesi manapun sejauh ini (bukan hanya belum selesai, tapi belum pernah dimulai sepengetahuan data yang tersedia).**

| Sub-klaim | Output ID (placeholder) | Status |
| --- | --- | --- |
| Simulasi rekomendasi alokasi tenaga skrining per provinsi | `OUT-TBL-RQ4` *(belum ada)* | PENDING |

---

## 2. Novelty Claim Audit

Klaim diambil dari `OUT-SRC-PITCH` (dek proposal asli) dan istilah wajib di `manuscript-outline-v1.md` (**OUT-SRC-OUTLINE**). Setiap baris: klaim asli, sumber, bukti terkini, output ID, dan verdict. **Verdict "Not yet supported" atau "Superseded" berarti klaim tersebut TIDAK BOLEH dinyatakan sebagai hasil tercapai di manuskrip sampai ada bukti.**

| # | Klaim | Sumber | Bukti Terkini | Output ID | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Sistem AI terintegrasi 6-layer (Data, Analytics, Spatial AI, Predictive Model, Optimization Model, Dashboard) | OUT-SRC-PITCH hlm. 3 | Data Layer: sebagian (climate feature engineering QA lulus). Spatial AI Layer: sebagian (LISA bulanan, bukan KMeans/DBSCAN/composite risk index seperti direncanakan). Analytics, Predictive Model, Optimization Model, Dashboard: **tidak ada bukti**. | OUT-QA-M1, OUT-TBL-M1 | **Partial** — 2 dari 6 layer punya bukti sebagian, 4 layer tanpa bukti |
| 2 | "TB Risk Map" Surabaya, tervalidasi ≥80% vs ground truth Dinkes (Milestone M3) | OUT-SRC-PITCH hlm. 3, 12 | Scope sudah pindah ke 38 provinsi nasional (bukan Surabaya/kecamatan); tidak ada validasi ground truth Dinkes; hasil LISA aktual justru **null** (seluruh 38 provinsi "Not significant" setelah FDR) | OUT-TBL-M1, `manuscript-methods-v0.8.md` §10 | **Superseded & not supported** — kriteria sukses asli tidak berlaku untuk scope aktual, dan bukti yang ada bertentangan dengan framing "risk map" yang confident |
| 3 | Prediksi kasus 3 bulan ke depan, MAPE ≤15% (Milestone M4) | OUT-SRC-PITCH hlm. 12 | Tidak ada model forecasting yang dijalankan; `[S3-STE-02]` belum tersedia | — | **Not yet supported** |
| 4 | Early Warning System (EWS) via ARIMA/XGBoost/Random Forest | OUT-SRC-OUTLINE (istilah wajib); OUT-SRC-PITCH hlm. 10 | Model yang benar-benar dijalankan (Task 3/5/6) adalah **PPML** (regresi panel asosiasi eksposur-outcome), **bukan** ARIMA/XGBoost/RF (time-series forecasting). Dua keluarga model berbeda tujuan. Ditambah: main effect iklim di PPML-nya sendiri **null** (Section 1.1.1) — bahkan sebagai model asosiasi pun belum menunjukkan sinyal prediktif kuat, apalagi diklaim sebagai dasar EWS. | OUT-MDL-T3-ALL | **Mismatch/unclear + belum ada sinyal pendukung** — perlu klarifikasi tim: apakah PPML dimaksudkan menggantikan EWS, atau EWS masih dibangun terpisah; dan jika terpisah, hasil PPML saat ini belum memberi dasar optimisme soal predictability |
| 5 | Resource Optimization via Integer Linear Programming (ILP) | OUT-SRC-OUTLINE (istilah wajib); OUT-SRC-PITCH hlm. 11 | Tidak ada task/output ILP di data manapun yang tersedia | — | **Not yet supported** |
| 6 | Spatial Autocorrelation (Moran's I / Getis-Ord Gi*) untuk deteksi klaster | OUT-SRC-OUTLINE (istilah wajib) | Local Moran's I (LISA) bulanan benar-benar dijalankan dan divalidasi; Global Moran's I dan Getis-Ord Gi* **belum** dijalankan | OUT-TBL-M1, OUT-VAL-M1 | **Partial — Supported untuk Local Moran's I saja** |
| 7 | "Model replikabel nasional" sebagai dampak sosial jangka panjang dari model Surabaya | OUT-SRC-PITCH hlm. 3 | Proyek **langsung** berpindah ke scope nasional karena keterbatasan akses data Dinkes Surabaya (institutional gatekeeping), bukan karena model Surabaya berhasil divalidasi lalu direplikasi. Causal story-nya berbeda dari klaim asli. | `manuscript-outline-v1.md` §Problem Statement | **Not supported as originally framed** — jangan disajikan seolah-olah pivot nasional = pencapaian tujuan replikasi; perlu di-reframe jujur di Introduction/Discussion |
| 8 | Referensi #8 di daftar pustaka pitch: "Barman, S., et al. (2025)... arXiv:2503.XXXXX" | OUT-SRC-PITCH hlm. 15 | ID arXiv literal berisi placeholder "XXXXX" — bukan referensi yang bisa ditelusuri/diverifikasi | OUT-SRC-PITCH hlm. 15 | **Tidak valid** — jangan dikutip di manuskrip sampai referensi asli ditemukan/diverifikasi, atau dihapus |
| 9 | "Variabel prediktor dominan TB teridentifikasi" (RQ1, outline Results) | OUT-SRC-OUTLINE §Results 1 | PPML primer (Task 3) menunjukkan **tidak ada** main effect iklim yang signifikan (p 0,45–0,70 di ketiga variabel); yang ditemukan adalah interaksi terbatas dengan kerentanan sosial (Task 6), bersifat eksploratif dan sebagian di-flag unreliable | OUT-MDL-T3-ALL, OUT-MDL-T6-ALL | **Not supported as framed** — RQ1 perlu ditulis ulang sebagai temuan null main-effect + interaksi eksploratif terbatas, bukan "faktor dominan teridentifikasi" |

---

## 3. Isu Struktural yang Perlu Keputusan Tim

1. **Milestone & KPI asli (M1–M5, tabel KPI di OUT-SRC-PITCH hlm. 12–13)** seluruhnya berpatokan pada scope Surabaya/kecamatan dan validasi ground truth Dinkes (coverage ≥90% kecamatan, kesesuaian risk map ≥80% vs Dinkes, MAPE ≤15%, UAT ≥4/5). Kriteria ini **tidak otomatis berlaku** untuk scope 38-provinsi/data terbuka saat ini. Perlu keputusan eksplisit: ditulis ulang untuk scope baru, atau dinyatakan gugur/superseded di manuskrip.
2. **Daftar pustaka di pitch deck (OUT-SRC-PITCH hlm. 15, 10 referensi: WHO 2024, Kemenkes 2023, Dinkes Surabaya 2024, BPS 2024, Menon & Koura 2025, Dwinata et al. 2025, Cahyaningrum & Setiyadi 2024, Barman et al. 2025, Faurholt-Jepsen et al. 2024, Wulandini et al. 2025) berbeda total dari 10 studi di evidence matrix resmi (OUT-EVID)** — tidak ada satu pun yang tumpang tindih. Belum jelas apakah daftar pustaka pitch pernah melalui proses vetting yang sama dengan evidence matrix. Rekomendasi: perlakukan OUT-EVID sebagai daftar yang authoritative untuk manuskrip; daftar pitch perlu diverifikasi ulang satu per satu sebelum dipakai (lihat juga isu #8 di tabel audit).
3. Klaim #4 (EWS vs PPML) sebaiknya diklarifikasi ke tim modeling sebelum Sprint 4 selesai, karena berimplikasi langsung pada spesifikasi model dan terminologi wajib manuskrip.

---

## 4. Output ID Legend (Baru + Reuse dari v0.8)

| Output ID | File sumber | Isi |
| --- | --- | --- |
| OUT-SRC-PITCH | `TBINSIGHT_LongTerm_IRIS_Project_Final_Draft.pdf` | Dek proposal/rekrutmen proyek asli (15 hlm., scope Surabaya) |
| OUT-SRC-OUTLINE | `manuscript-outline-v1.md` | Outline manuskrip & glossary istilah wajib/terlarang |
| OUT-EVID | `TBINSIGHTliteratureevidencematrix.xlsx` | Matriks evidence 10 studi literatur |
| OUT-QA-M1 | `results/qa/feature_matrix_qa.md` | Laporan QA feature matrix iklim (reuse dari v0.8) |
| OUT-TBL-M1 / M2 / M3 | `hotspot_persistence_R.csv` / `_raw_R.csv` / `hotspot_stability_transitions_R.csv` | Hasil persistence LISA (reuse dari v0.8) |
| OUT-DAT-M1 | `hotspot_monthly_lisa_R.csv` | Hasil LISA bulanan mentah (reuse dari v0.8) |
| OUT-VAL-M1 | `hotspot_persistence_validation_R.json` | Manifest validasi S3-DAM-01 (reuse dari v0.8) |
| OUT-MDL-T3-TEMP / T3-PRECIP / T3-HUM | `results/models/baseline_ppml/{temperature,precipitation,humidity}/coefficients.csv` | Task 3 (revised) — 3 model primary single-exposure |
| OUT-MDL-T3-JOINT | `results/models/baseline_ppml/joint_sensitivity/coefficients.csv` | Task 3 — model sensitivity (joint, 3 exposure bareng) |
| OUT-MDL-T3-ALL | `coefficients_all_models.csv` | Task 3 — ringkasan cross-model |
| OUT-MDL-T3-META | `metadata_all_models.json` | Task 3 — metadata & rationale revisi struktur |
| OUT-MDL-T5-ALL | `coefficients_all_lags.csv` | Task 5 — ringkasan 9 model lag individual |
| OUT-MDL-T5-RULE | `selection_rule.md` | Task 5 — aturan pre-specified anti-cherry-picking lag |
| OUT-MDL-T5-SKIP | `skipped_models.csv` | Task 5 — daftar model lag3/lag0-3 yang tidak dijalankan (variabel tidak ada di panel) |
| OUT-MDL-T6-ALL | `coefficients_all_interactions.csv` | Task 6 — ringkasan 9 model interaksi iklim×kerentanan |
| OUT-MDL-T6-ISSUE | `issue_log.md` | Task 6 — log isu data (T6-01 poverty, T6-02 density, T6-03 time-invariance) |
| OUT-MDL-T6-MULT | `multiplicity_note.md` | Task 6 — catatan non-adjustment multiple testing |
| OUT-TBL-RQ3 / RQ4 | *(belum ada)* | Placeholder — akan diisi saat data forecasting/ILP tersedia |

---

## 5. Items Requiring Input Before v1.0

- [ ] Hasil forecasting time-series (RQ3) dan task/output ILP (RQ4) — masih belum ada sama sekali.
- [ ] Perbaikan data `poverty_pct` (isu T6-01) lalu re-run `run_task6_social_interactions.py` sebelum ketiga model `*_x_poverty` bisa dilaporkan.
- [ ] Keputusan tim atas isu struktural #1–#3 di Section 3.
- [ ] Klaim #4 (EWS vs PPML) — makin mendesak diklarifikasi sekarang karena hasil PPML utama sendiri null; berimplikasi ke framing seluruh RQ1 dan RQ3.
- [ ] Verifikasi referensi #8 pitch deck (arXiv placeholder) sebelum dipakai di manapun.
- [ ] Pertimbangkan log-transform `population_density_per_km2` (isu T6-02) sebagai amandemen eksploratif terpisah sebelum mengutip hasil `*_x_density` sebagai final.