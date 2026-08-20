# TB-INSIGHT — Rencana Sprint 6 Minggu

Periode kerja: **Senin, 24 Agustus 2026–Minggu, 4 Oktober 2026**  
Produk: **TB-INSIGHT Product Ongoing Real Data**  
Fokus: penelitian ekologi spatio-temporal TB tingkat provinsi dan dashboard berbasis data nyata.

## 1. Sasaran akhir enam minggu

Pada akhir Sprint 6, tim harus memiliki:

1. panel analisis 38 provinsi × 24 bulan yang terversi, tervalidasi, dan dapat direproduksi;
2. EDA nasional/provinsi, analisis temporal, Global Moran's I, LISA, dan hotspot persistence;
3. model PPML fixed effects dengan offset populasi, lag iklim terbatas, interaksi sosial terpilih, serta sensitivity analysis;
4. dashboard research-ready yang menampilkan provenance, status data, metode, dan keterbatasan;
5. manuskrip lengkap beserta tabel, gambar, supplementary material, dan reproducibility appendix;
6. satu release candidate yang dapat didemonstrasikan tanpa mencampur data sintetis.

Outcome utama wajib disebut **pasien mulai pengobatan TBC sensitif obat (`treatment_started`)**, bukan insidensi TB. Hasil dua tahun adalah asosiasi eksploratif, bukan klaim kausal atau forecasting operasional. Data 2025 tetap diberi label provisional.

## 2. Struktur ClickUp yang disarankan

```text
Space: TB-INSIGHT
└── Folder: Product Ongoing — Real Data
    ├── List: S1 Foundation & Data Freeze
    ├── List: S2 EDA & Spatial Foundation
    ├── List: S3 Climate, Social & Prototype
    ├── List: S4 Sensitivity & Integration
    ├── List: S5 Release Candidate
    └── List: S6 Final Validation & Handover
```

Status: `BACKLOG → READY → IN PROGRESS → IN REVIEW → BLOCKED → DONE`.

Custom fields minimum:

- `Workstream`: Data, Modeling, Spatial, Product, Writing, QA;
- `Sprint`: S1–S6;
- `Primary Owner`;
- `Reviewer`;
- `Deliverable Path`;
- `Acceptance Criteria`;
- `Dependency IDs`;
- `Effort Hours`;
- `Evidence Link`;
- `Data Status`: Frozen, Provisional, Not Applicable;
- `Risk`: Low, Medium, High.

Gunakan task ID di workbook sebagai prefix nama task, misalnya `[S2-VEN-01] National and province EDA` agar dependency tetap terbaca setelah import.

### Cara import workbook

1. Buat status dan Custom Fields di ClickUp terlebih dahulu.
2. Buka importer Spreadsheet dan unggah `deliverables/TB_INSIGHT_ClickUp_6_Week_Sprint_Plan.xlsx`.
3. Pilih worksheet pertama, `ClickUp Import`, lalu gunakan format tanggal `Year-Month-Day`.
4. Petakan `Task Name` ke field Task Name; petakan Assignee, Status, Priority, Start Date, Due Date, dan Tags ke native fields.
5. Petakan Task ID, Reviewer, Sprint, Workstream, Dependency IDs, Effort Hours, Deliverable Path, Acceptance Criteria, Risk, dan Data Status sebagai Custom Fields.
6. Periksa live preview. Setelah import, ubah task M1–M6 menjadi Milestone dan buat native task dependencies menggunakan kolom Dependency IDs.

ClickUp saat rencana ini dibuat mendukung impor `.xlsx`, dengan satu baris sebagai satu task dan Task Name sebagai satu-satunya field wajib. Mapping lengkap tersedia pada worksheet `ClickUp Mapping`.

## 3. Pembagian peran dan ownership

| Anggota | Peran utama | Ownership | Reviewer utama |
|---|---|---|---|
| Venedict | Data Scientist — data/QA lead | pipeline, data freeze, EDA, feature engineering, reproducibility | Stephen |
| Stephen | Data Scientist — modeling lead | analysis plan, PPML, lag/interaksi, sensitivity, model reporting | Venedict |
| Dame | Spatial Analyst — spatial lead | boundary, spatial weights, Moran/LISA, hotspot, cartography | Erin / Stephen |
| Erin | UI/UX Designer — product lead | information architecture, design system, frontend, API integration, usability | Dame / Venedict |
| Adzki | Scientific Writer — evidence lead | literature matrix, manuscript, terminology, limitation, supplement | seluruh lead teknis |

Tidak ada output analisis yang dianggap final sebelum direview oleh orang kedua. Adzki tidak menunggu Sprint 5 untuk menulis; manuskrip dibangun sejak Sprint 1.

## 4. Kalender sprint dan milestone

| Sprint | Tanggal | Fokus | Exit milestone |
|---|---|---|---|
| S1 | 24–30 Agustus | fondasi, protokol, QA, IA | **M1 — Data & Question Freeze** |
| S2 | 31 Agustus–6 September | EDA, baseline, spatial weights, wireframe | **M2 — Descriptive & Spatial Foundation** |
| S3 | 7–13 September | iklim, sosial, hotspot, frontend alpha | **M3 — Analysis Alpha** |
| S4 | 14–20 September | sensitivity, residual spatial, integrasi | **M4 — Analysis Freeze** |
| S5 | 21–27 September | publication outputs, UX test, manuscript | **M5 — Release Candidate** |
| S6 | 28 September–4 Oktober | independent reproduction, QA, handover | **M6 — Final Research Package** |

## 5. Alur tiap sprint

### Sprint 1 — Foundation & Data Freeze

Tujuan: membekukan pertanyaan penelitian, versi data, definisi variabel, dan kontrak visual sebelum analisis berkembang.

- Venedict menjalankan pipeline dari snapshot mentah, membuat checksum, QA report, dan memperbarui data dictionary/source ledger.
- Stephen mengunci outcome primer, offset, estimand, model primer, lag 0–3, serta daftar sensitivity analysis.
- Dame mengaudit batas 38 provinsi, CRS, centroid, neighbor islands/Papua, dan rancangan spatial weights.
- Erin menyusun information architecture, user flow, component inventory, serta aturan status provisional/provenance.
- Adzki membuat literature evidence matrix, outline manuskrip, glossary, dan kerangka Introduction–Methods.
- Seluruh tim melakukan gate review M1. Tidak ada feature/model baru tanpa decision log setelah gate.

### Sprint 2 — EDA & Spatial Foundation

Tujuan: menghasilkan gambaran deskriptif yang benar sebelum model inferensial.

- Venedict membuat EDA nasional/provinsi: count, population rate, tren, missingness, outlier, seasonality deskriptif, dan data maturity.
- Stephen membangun baseline PPML, membandingkan count/rate secara deskriptif, dan menghasilkan diagnostics dasar.
- Dame memfinalkan adjacency/weights berversi, Global Moran's I, LISA awal, dan sensitivity neighbor definition.
- Erin membuat wireframe high-fidelity untuk Overview, Trend, Map/Hotspot, Methods, dan Data Sources.
- Adzki menyelesaikan draft Data & Methods serta tabel karakteristik deskriptif dengan footnote yang benar.
- Gate M2 hanya lulus bila angka dashboard, tabel, dan narasi berasal dari output pipeline yang sama.

### Sprint 3 — Climate, Social & Prototype

Tujuan: menguji novelty iklim dan kerentanan sosial tanpa overfitting.

- Venedict membuat anomali/z-score iklim, lag 0–3, definisi seasonality yang sesuai Indonesia, serta QA feature matrix.
- Stephen menjalankan PPML lag iklim satu per satu, interaksi sosial pre-specified, dan dokumentasi multiple testing.
- Dame menganalisis hotspot persistence dan perbedaan pola menurut anomali iklim/kerentanan sosial.
- Erin membangun frontend alpha dan menghubungkan komponen ke schema API tervalidasi.
- Adzki memperbarui Methods, membuat Results shell, serta memastikan klaim novelty didukung literatur.
- Gate M3 memilih model kandidat berdasarkan protokol dan robustness, bukan hanya p-value.

### Sprint 4 — Sensitivity & Integration

Tujuan: menguji apakah temuan bertahan terhadap keterbatasan data dan menyatukan analisis dengan produk.

- Venedict menjalankan sensitivity data maturity 2025, kejadian bencana, outlier, alternative denominator, dan exclusion checks.
- Stephen memeriksa residual spatial autocorrelation, alternative specifications, uncertainty, dan final model comparison.
- Dame memfinalkan LISA/persistence, island/Papua sensitivity, dan audit konsistensi kode–nama–geometri.
- Erin menyambungkan frontend–backend, provenance panel, download/export, empty/error state, dan accessibility dasar.
- Adzki menulis draft lengkap Introduction–Methods–Results awal–Limitations dan merekonsiliasi setiap angka.
- Gate M4 membekukan angka utama, tabel utama, dan peta utama. Perubahan setelahnya memerlukan change request.

### Sprint 5 — Release Candidate

Tujuan: mengubah output teknis menjadi paket yang siap direview eksternal.

- Venedict memfinalkan pipeline release, codebook, QA report, analytical tables, dan manifest output.
- Stephen memfinalkan model tables/figures, robustness appendix, serta plain-language interpretation.
- Dame menghasilkan peta publikasi dengan legenda, skala, proyeksi, uncertainty note, dan alt-text.
- Erin menjalankan usability test, memperbaiki hierarchy/responsiveness, dan menyiapkan dashboard release candidate.
- Adzki menyelesaikan manuskrip v1, abstract, discussion, references, supplement, dan reproducibility appendix.
- Gate M5 mencakup demo internal, scientific review, dan daftar defect P0/P1/P2.

### Sprint 6 — Final Validation & Handover

Tujuan: memastikan orang lain dapat mereproduksi, memahami, dan mendemonstrasikan hasil.

- Venedict melakukan clean-environment reproduction dan membuat data/model release manifest.
- Stephen melakukan independent rerun serta sign-off kecocokan angka model dan interpretasi.
- Dame melakukan final spatial/cartographic QA dan menyerahkan spatial assets terversi.
- Erin menutup defect P0/P1, melakukan end-to-end dashboard QA, dan menulis handover produk.
- Adzki memfinalkan manuskrip, reference audit, figure/table callout, cover summary, dan submission checklist.
- Seluruh tim menjalankan dry run presentasi dan go/no-go review M6.

## 6. Ritme kerja mingguan

- **Senin, 09.00–09.45:** sprint planning; pilih task READY, cek kapasitas dan dependency.
- **Selasa–Kamis, 09.00–09.15:** async-first daily check-in: done, next, blocker, evidence link.
- **Rabu, 15.30–16.15:** technical sync untuk data–model–spatial–UI–writing contract.
- **Jumat, 14.00:** code/output freeze sprint.
- **Jumat, 15.30–16.30:** demo dan evidence review.
- **Jumat, 16.30–17.00:** retrospective dan keputusan carry-over.

Batasi work in progress menjadi maksimal dua task aktif per orang. Blocker yang tidak selesai dalam satu hari harus berubah menjadi status `BLOCKED`, ditandai owner dependency, dan dibahas pada sync terdekat.

## 7. Definition of Ready

Task hanya boleh masuk `IN PROGRESS` jika:

- owner dan reviewer sudah ada;
- input file/API dan versi disebutkan;
- dependency selesai atau tersedia;
- acceptance criteria dapat diuji;
- deliverable path sudah ditentukan;
- istilah outcome dan unit analisis tidak ambigu.

## 8. Definition of Done

Task hanya boleh ditutup jika:

- output tersimpan pada path yang disepakati dan evidence link terisi;
- script/notebook berjalan ulang dari input terversi;
- reviewer menandatangani acceptance criteria;
- angka memiliki unit, periode, definisi, dan provenance;
- data 2025/provisional ditandai bila relevan;
- tidak ada data synthetic pada product ongoing;
- klaim membedakan fakta, interpretasi, dan hipotesis;
- dokumentasi dan decision log diperbarui.

## 9. Quality gates

### M1 — Data & Question Freeze

- panel 912 baris, 38 provinsi, 24 bulan;
- tidak ada duplicate key/missing variabel wajib;
- outcome primer dan model primer tertulis;
- spatial IDs dan UI data contract disetujui;
- literature matrix dan outline tersedia.

### M4 — Analysis Freeze

- model primer dan seluruh sensitivity pre-specified selesai;
- residual spatial autocorrelation diperiksa;
- tabel/peta utama memiliki provenance;
- angka dashboard dan manuskrip berasal dari output yang sama;
- limitation dua tahun dan provisional 2025 terlihat jelas.

### M6 — Final Research Package

- clean rerun berhasil oleh orang selain pembuat script utama;
- dashboard tidak memiliki defect P0/P1;
- semua angka manuskrip direkonsiliasi;
- README, codebook, source ledger, supplement, dan handover lengkap;
- final sign-off dari lima anggota.

## 10. Risiko utama dan mitigasi

| Risiko | Mitigasi | Owner |
|---|---|---|
| Seri waktu hanya 24 bulan | batasi klaim, lag 0–3, tidak membuat forecasting operasional | Stephen / Adzki |
| Outcome disalahartikan sebagai insidensi | terminology audit pada dashboard, tabel, dan manuskrip | Adzki |
| Data 2025 provisional | maturity flag, sensitivity analysis, visible warning | Venedict / Erin |
| Overfitting iklim dan sosial | spesifikasi pre-defined, uji satu interaksi per model, multiple-testing note | Stephen |
| Definisi neighbor provinsi kepulauan | weights terversi dan sensitivity alternatif | Dame |
| UI tidak sinkron dengan hasil | output manifest dan API contract; tidak ada angka hardcoded | Erin / Venedict |
| Penulisan tertinggal | writing berjalan dari Sprint 1 dan weekly claim audit | Adzki |

## 11. Aturan prioritas saat waktu tertekan

Urutan yang tidak boleh dikorbankan:

1. integritas data dan reproducibility;
2. kejelasan outcome serta limitation;
3. model primer dan sensitivity inti;
4. peta/tabel utama;
5. manuskrip dan dashboard yang konsisten;
6. fitur tambahan atau kosmetik.

Jika kapasitas berkurang, kurangi animasi, fitur dashboard tambahan, dan model eksploratif. Jangan mengurangi QA, provenance, independent rerun, atau limitation disclosure.
