# TB-INSIGHT — API–UI Data Contract

## 1. Identitas, status, dan batas dokumen

| Item | Nilai |
| --- | --- |
| Task | S2-ERI-02 — API–UI data contract |
| Status | DRAFT v0.1 — untuk review backend, frontend, dan penanggung jawab data/metode |
| Tanggal penyusunan | 2026-09-14 |
| Produk | `product-ongoing-real-data/` |
| Target penempatan dalam repository | `product-ongoing-real-data/docs/design/api-ui-contract.md` |
| Referensi desain | `tb-insight-wireframe-s2-eri-01.html` — S2-ERI-01 |
| Referensi implementasi | Lampiran `main.py` |
| Acceptance criteria | Tidak ada angka hardcoded; setiap widget memetakan field, unit, source, dan fallback |

Dokumen ini mencakup **enam halaman**: Overview, Trend, Map, Detail Provinsi, Methods, Sources; komponen global, tooltip, SourceDrawer, navigasi, unduhan, dan seluruh state pada desain juga dicakup.

Dasar pemeriksaan adalah dua lampiran, bukan checkout repository atau API yang sedang berjalan. CSV processed, codebook, source ledger, hasil validasi, dan hasil model tidak disertakan. Oleh karena itu:

- **EXISTING** berarti implementasi terlihat langsung di `main.py`; tidak berarti endpoint sudah diuji menggunakan dataset sebenarnya.
- **PROPOSED** berarti kontrak target yang diusulkan dokumen ini; belum tersedia di `main.py`.
- **BLOCKED-DATA** berarti nama kolom sumber, definisi, atau artefak masih harus diverifikasi sebelum implementasi dinyatakan selesai.
- **BACKLOG** berarti fitur belum boleh menampilkan hasil; boleh ditampilkan sebagai kemampuan yang belum tersedia.

Semua nama field `/api/v1/*` di bawah adalah schema target, bukan klaim nama kolom CSV yang sudah ada. Contoh URL adalah contoh request, bukan bukti endpoint aktif. Tidak ada data penelitian baru yang dibuat dalam tugas dokumentasi ini.

### 1.1 Jejak lampiran yang diperiksa

| Lampiran | SHA-256 |
| --- | --- |
| `main.py` | `9a03f78fd88a83229bbccfdf07e1215abf3b4107da1c9f7ec04505bcb32aad1a` |
| `tb-insight-wireframe-s2-eri-01.html` | `a1fc90c9bf34b75b8d98ebf958529a4bdd0905c667b9f51b69e7569087e04cc2` |

Hash tersebut hanya mengidentifikasi lampiran yang direview, **bukan checksum dataset** dan bukan bukti QA panel.

## 2. Prinsip kontrak

1. Outcome utama adalah **pasien memulai pengobatan TBC sensitif obat**, bukan estimasi insidensi, seluruh notifikasi, atau seluruh kasus TB.
2. Semua nilai data, cakupan, periode tersedia, sumber aktif, tanggal snapshot, hasil QA, dan status model berasal dari API/artefak tervalidasi; tidak dari konstanta wireframe.
3. Setiap nilai harus dapat ditelusuri ke definisi field, unit, sumber, versi dataset, serta transformasi bila merupakan nilai turunan.
4. Nilai `0`, `null`, baris tidak ada, endpoint belum tersedia, dan request gagal adalah kondisi berbeda.
5. Angka sintetis, skor risiko, forecast, dan optimasi dari `product-demo-synthetic/` tidak boleh menjadi fallback.
6. Status sumber resmi, status revisi snapshot, kematangan outcome, dan status QA adalah dimensi yang berbeda; jangan disatukan menjadi satu badge.
7. BPS tetap tahunan/periode survei. Pengulangan nilai dalam panel bulanan adalah konteks penggabungan, bukan observasi bulanan atau interpolasi.
8. Perubahan filter harus memengaruhi data, judul, satuan, tooltip, source note, dan unduhan secara konsisten.
9. Data yang belum tersedia tidak memakai skeleton tanpa akhir. Skeleton hanya untuk request yang sedang berlangsung.
10. Kata-kata kausal dan label hotspot/risiko tidak diturunkan dari warna, ranking, atau z-score deskriptif.

### 2.1 Definisi larangan hardcoded

**Dilarang di production UI:** nilai pasien/rate/pending share, angka provinsi/bulan/baris/sumber aktif, tanggal frozen/updated, status QA PASS, nilai outlier, threshold analitik tanpa referensi metode, angka model, nilai sosial/bencana, serta koordinat SVG/tinggi batang yang mengodekan angka ilustratif.

**Boleh sebagai konfigurasi presentasi:** ukuran grafik, warna, jumlah desimal, label navigasi, dan batas overlay tiga provinsi sebagai keputusan UX. Konstanta matematis `100000` untuk skala rate dan `100` untuk persen boleh ada dalam formula terdokumentasi. Ambang kematangan adalah konfigurasi metode berversi dari backend, bukan konstanta tersembunyi frontend.

Tanggal penyusunan dokumen dan angka pada test fixture bukan data dashboard. Fixture pengujian harus diberi label test-only dan tidak diimpor bundle produksi.

## 3. Audit kontrak EXISTING di `main.py`

### 3.1 Katalog route aktual

Semua endpoint data berikut menggunakan `GET`, tanpa query parameter yang dideklarasikan, tanpa `response_model`, dan tanpa envelope `{data, meta}`. Menambahkan `?province_code=...` ke URL aktual tidak membuktikan filter diterapkan; fungsi tidak membaca parameter itu.

| ID | Path EXISTING | Sumber di kode | Bentuk respons aktual | Catatan |
| --- | --- | --- | --- | --- |
| L0 | `/` | `frontend/dist/index.html` jika tersedia | HTML; selain itu objek `message` | Bukan endpoint data |
| L1 | `/api/summary` | `tb_province`, `tb_month`, `tb_province_month` | Objek ringkasan, rincian §3.2 | `503` jika annual TB atau national month kosong; belum memeriksa kesiapan monthly outcomes secara memadai |
| L2 | `/api/tb/national-monthly` | `tb_national_month_official.csv` | Array semua kolom CSV | `period` dan `indicator` terlihat dipakai kode; nama kolom nilai belum terverifikasi |
| L3 | `/api/tb/province-annual` | `tb_province_annual_official.csv` | Array semua kolom CSV | Kode memakai `province_code`, `province`, `year`, `tb_cases_total` |
| L4 | `/api/tb/province-monthly-treatment-outcomes` | `tb_treatment_outcomes_province_month_official.csv` | Array semua kolom CSV | Kolom outcome belum dapat dikonfirmasi dari kode ini saja |
| L5 | `/api/bps/province-annual` | `bps_province_annual_official.csv` | Array semua kolom CSV | Kode merujuk `province_code`, `province`, `year`; nama indikator BPS belum terverifikasi |
| L6 | `/api/analysis/province-2024` | Merge annual TB dengan BPS yang difilter `year == 2024` | Array hasil merge | Bukan panel provinsi-bulan TB–iklim–bencana; suffix `_kemenkes`/`_bps` hanya untuk kolom non-key yang bertabrakan |
| L7 | `/api/metadata` | Literal dictionary dalam Python | `{sources: [...], limitations: [...]}` | Empat entri dataset sumber dan empat limitation statis; bukan pembacaan source ledger |

`records()` mengubah pandas missing values menjadi JSON `null`; frame kosong menjadi `[]`. Belum ada pengurutan atau penyaringan eksplisit pada route array. `province_code` dibaca sebagai string dan di-padding dua karakter ketika kolom tersedia. Keunikan key, tipe kolom lain, nilai non-finite, dan cakupan dataset belum dijamin route.

### 3.2 Schema ringkasan L1 yang benar-benar terlihat

| Field aktual | Tipe dari kode | Arti/perilaku aktual | Batas pemakaian UI |
| --- | --- | --- | --- |
| `province_reference_year` | integer | Literal `2024` | Belum dinamis dari dataset |
| `province_count` | integer | Jumlah kode provinsi unik di annual TB | Bukan jumlah provinsi lengkap pada filter monthly |
| `tb_cases_2024` | integer | Sum `tb_cases_total` seluruh frame annual TB | Tidak memfilter tahun sebelum sum; tidak boleh dipakai sebagai KPI treatment initiation bulanan |
| `national_month_period_min`, `national_month_period_max` | string | Min/max `tb_month.period` | Cakupan seri nasional, bukan otomatis cakupan panel penelitian |
| `national_month_indicators` | integer | Jumlah indikator unik nasional | Bukan jumlah pasien |
| `latest_series_period` | string | Periode baris terakhir setelah sort `period` | Tidak membawa nilai indikator tertentu |
| `province_month_rows` | integer | Panjang frame monthly outcomes | Bukan otomatis jumlah key provinsi-bulan unik atau panel final |
| `province_month_period_min`, `province_month_period_max` | string | Min/max `tb_province_month.period` | Akses bisa gagal jika kolom tidak ada |
| `province_month_status` | string | Narasi statis cakupan kohort | Jangan parse narasi sebagai hitungan/freshness |

### 3.3 Perilaku operasional dan gap backend

- CSV dibaca saat modul di-load. Mengubah file setelah proses berjalan tidak otomatis memperbarui DataFrame; jangan menyebut API live-refresh.
- File tidak ada menghasilkan frame kosong, tetapi kegagalan parse/read/merge tidak seluruhnya ditangani. Merge `validate="one_to_one"` dapat menggagalkan startup jika key tidak unik.
- L6 melakukan left join seluruh annual TB ke BPS tahun tertentu. Jika annual TB berisi tahun lain, baris itu dapat tetap ada dengan BPS kosong; nama route saja tidak menjamin isi hanya satu tahun.
- Error terkontrol L1 memakai bentuk FastAPI `{"detail":"Curated official datasets are not ready"}`, bukan schema error usulan §7.
- Route wildcard `/{file_name:path}`, bila static directory tersedia, dapat mengembalikan HTML index untuk path API yang tidak dikenal. UI tidak boleh menganggap HTTP 200 non-JSON sebagai data valid; target backend harus mengecualikan `/api/*` dari fallback SPA.
- Belum ada manifest rilis, metadata per field, endpoint iklim/bencana/peta/model/ekspor, maupun laporan freshness dan QA terstruktur.

## 4. Pemetaan sumber dan verifikasi nama kolom

Kode sumber di bawah adalah **ID kontrak usulan** yang harus dipetakan ke entry ledger sebenarnya; bukan ID ledger yang sudah dikonfirmasi.

| Source ID usulan | Dasar yang terlihat | Peran | Status verifikasi |
| --- | --- | --- | --- |
| `sitb_cohort` | L4 dan metadata SITB kohort | Numerator treatment initiation dan outcome | File dirujuk; kolom dan snapshot BLOCKED-DATA |
| `satusehat_national` | L2 dan metadata Pemantauan Kasus Tuberkulosis | Seri nasional resmi terpisah | Jangan disamakan otomatis dengan agregat L4 |
| `kemenkes_profile` | L3, Profil Kesehatan Indonesia 2024 Lampiran 56.a pada metadata | Indikator TB annual | Tidak menggantikan outcome kohort monthly |
| `bps` | L5 dan metadata BPS | Populasi dan konteks sosial | Satuan populasi dan periode survei perlu codebook |
| `nasa_power` | Wireframe | Kovariat iklim | Belum di-load `main.py`; artefak dan metode perlu verifikasi |
| `big` | Wireframe | Referensi batas/agregasi spasial | Bukan pemasok angka TB; versi batas belum tersedia |
| `bnpb` | Wireframe | Bencana, sensitivitas sekunder | Endpoint/rekonsiliasi belum terverifikasi |
| `who_reference` | Wireframe | Rujukan metodologi/konteks | Bukan sumber angka panel utama kecuali lineage membuktikannya |
| `project_validation` | Wireframe menyebut ledger, validasi, frozen release | Provenance internal/QA | Bukan instansi sumber epidemiologi eksternal |
| `project_analysis` | Wireframe menyebut calendar summary, outliers, PPML | Hasil olahan internal | Wajib lineage ke input resmi dan metode berversi |

**Jangan menetapkan jumlah sumber menjadi 7.** Metadata Python berisi empat entry dataset, bukan empat publisher unik. Wireframe berisi enam sumber bernama dan satu `pending7`, sekaligus menyebut empat sumber tambahan; daftar itu belum rekonsiliasi. Hitung dataset aktif dan publisher unik sebagai dua metrik terpisah dari ledger terverifikasi. Entry placeholder tidak dihitung aktif; WHO sebagai referensi tidak otomatis dihitung sebagai input numerik panel.

### 4.1 Registry alias yang harus diselesaikan sebelum integrasi

| Field target | Referensi yang diketahui | Keputusan |
| --- | --- | --- |
| `province_code` | Nama terlihat di Python | Normalisasi kode resmi string dua digit; validasi terhadap master berversi |
| `province_name` | Python memakai `province` untuk merge | Alias setelah header CSV diperiksa |
| `period` | Python memakai `period` | Format aktual harus dibuktikan sesuai `YYYY-MM` |
| `treatment_started` | Wireframe menyebut `jumlah_pasien`; glossary menyebut `treatment_started` | Kandidat alias saja; pastikan definisi numerator dan tipe dari codebook |
| `outcome_pending` | Wireframe menyebut `belum_ada_hasil` | Kandidat alias; cek denominator dan kategori outcome |
| `population`, `population_density`, `poverty_pct`, `sanitation_pct` | Nama kolom tidak terlihat di Python | BLOCKED-DATA; jangan menebak header atau skala persen |
| `temperature_c_z`, `humidity_z`, `precipitation_z` | Nama disebut wireframe sebagai field yang dibutuhkan | Belum bukti kolom aktual atau endpoint |
| `count_zscore` | Badge detail dan outlier wireframe | Perlu file hasil, definisi baseline, dan method ID |

Deliverable implementasi tambahan yang dibutuhkan: mapping `source_file → source_column → canonical_field → unit_conversion → method_id`, diuji menggunakan CSV/codebook aktual. `tb_cases_total` tidak boleh diberi alias `treatment_started` tanpa bukti kesamaan definisi.

## 5. Strategi kontrak target dan filter

### 5.1 Versioning

Kontrak target menggunakan prefix **`/api/v1` (seluruhnya PROPOSED)** agar perubahan array legacy menjadi envelope tidak merusak konsumen lama. Legacy `/api/*` dipertahankan sampai migrasi disepakati. `contract_version` terpisah dari `dataset_version` dan `method_version`.

Backend menggunakan schema eksplisit serta validasi respons; tidak meneruskan semua kolom CSV secara otomatis. Kolom baru tidak otomatis menjadi bagian kontrak. Breaking change memerlukan versi API baru atau proses migrasi yang disetujui.

### 5.2 State filter bersama

| Parameter | Tipe dan aturan | Default/scope |
| --- | --- | --- |
| `dataset_version` | ID rilis yang terdaftar manifest | UI resolve default release sekali, lalu pin semua request dalam satu sesi tampilan |
| `start_period`, `end_period` | Bulan valid `YYYY-MM`, inklusif; harus berpasangan; awal ≤ akhir | Dari cakupan penelitian di manifest, bukan literal wireframe |
| `province_code` | Satu kode dari master provinsi | Omit = seluruh provinsi dalam scope; bukan string `all` atau angka `0` |
| `period` | Satu bulan `YYYY-MM` | Bulan fokus KPI/Map/Detail; default akhir rentang aktif, tidak mundur diam-diam jika data hilang |
| `metric` | `count` atau `rate` | `count` pada Overview/Trend; Map memakai pilihan yang sama dan label mengikuti metrik |
| `overlay_province_codes` | Query berulang, kode unik, maksimum tiga | Hanya Trend; pilihan primer dan overlay tidak diduplikasi |
| `layer` | `tb`, `social`, `climate`, `disaster`, `consistent` | Map; `tb`; capability menentukan enabled/disabled |
| `indicator` | ID registry sesuai layer/endpoint | TB default `treatment_started`; sosial/iklim harus eksplisit dari opsi manifest |
| `year` | Integer yang tercantum cakupan indikator | Endpoint annual/social; pilih tahun dari periode fokus hanya jika memang tersedia |
| `lag_months` | Integer nonnegatif, anggota `supported_lags` manifest | Iklim; default dari method metadata, bukan mengarang lag yang belum diproduksi |
| `model_id` | ID artefak model yang terdaftar | Tidak menjalankan fit model lewat request UI |
| `language` | Bahasa yang didukung manifest | Methods, default `id`; bahasa belum tersedia → metadata unavailable, bukan fallback tanpa label |
| `limit`, `offset` | Integer positif/nonnegatif, dibatasi manifest | Outlier/history; respons mengembalikan pagination; jangan memangkas data diam-diam |
| `format` | `json` atau `csv` | Export, default `json` |

Endpoint hanya menerima parameter yang tercantum pada katalog §10. Parameter tak dikenal ditolak `422`; frontend tidak mengirim seluruh state URL secara buta ke setiap endpoint.

### 5.3 Semantik filter per halaman

- **Overview:** coverage strip menunjukkan rilis penuh dengan label “cakupan dataset”; kartu pasien/rate/pending dan “provinsi tersedia” mengikuti scope serta bulan fokus. Preview trend memakai rentang aktif; preview map memakai bulan fokus. Coverage global tidak boleh disamarkan sebagai hasil filter.
- **Trend:** nasional default adalah agregat kohort SITB dari provinsi dalam rilis, bukan otomatis L2. Jika satu provinsi dipilih, judul menjadi tren provinsi tersebut. Overlay mempertahankan unit/metrik dan bulan yang sama. Agregat nasional konteks tidak diubah menjadi “nasional” bila scope sudah subset.
- **Map:** peta snapshot bulanan pada `period`, bukan sum seluruh rentang. Semua provinsi referensi tetap dapat digambar; pilihan provinsi menyorot wilayah, bukan mengubah domain warna menjadi satu provinsi. Layer sosial memakai tahun/periode survei yang ditampilkan eksplisit.
- **Detail:** route membutuhkan kode provinsi; bulan yang diklik menjadi `period` tanpa menghilangkan rentang untuk grafik tren.
- **Methods:** tidak difilter provinsi; terikat rilis, versi metode, bahasa. Bagian hasil model memiliki scope model sendiri yang selalu terlihat.
- **Sources:** semua sumber rilis tetap terlihat; filter hanya dapat menyorot pemakaian, tidak mengubah jumlah sumber aktif rilis.
- **Reset:** tindakan eksplisit pengguna; kembalikan default dari manifest. Empty/error tidak boleh mereset filter otomatis.

URL UI menyimpan `page`, filter data, `source_id` drawer jika diperlukan, dan `from=trend|map` untuk navigasi detail. Parameter navigasi tidak dikirim ke API. Klik titik nasional tidak boleh membuka detail provinsi arbitrer; hanya titik yang memiliki `province_code` dapat drill-down ke provinsi.

Periode valid di luar cakupan mengembalikan `200` dengan `availability="unavailable"`, data kosong, alasan `OUTSIDE_COVERAGE`. Rentang sebagian beririsan mengembalikan data dalam cakupan dan peringatan partial. Bulan fokus harus di dalam rentang yang diminta; pelanggaran adalah `422`.

## 6. Schema bersama target

Notasi TypeScript berikut adalah spesifikasi bentuk JSON, bukan kode implementasi. Properti tanpa `?` wajib hadir; tipe `null` berarti ketidaktersediaan yang eksplisit. Angka JSON tidak boleh berupa string lokal, `NaN`, atau `Infinity`.

```typescript
type Availability = "available" | "partial" | "unavailable";
type EvidenceKind = "reported" | "derived" | "exploratory";
type RevisionStatus = "final" | "provisional" | "unknown";
type Maturity = "mature" | "immature" | "unknown" | "not_applicable";
type QAStatus = "passed" | "caution" | "failed" | "not_run";

interface Scope {
  geographic_level: "national" | "province" | "multi_province" | "release";
  province_codes: string[];
  start_period: string | null;
  end_period: string | null;
  focus_period: string | null;
}
interface Warning {
  code: string;
  message: string;
  affected_fields: string[];
  affected_keys: string[];
}
interface Coverage {
  period_min: string | null;
  period_max: string | null;
  province_count: number | null;
  month_count: number | null;
  expected_observations: number | null;
  observed_observations: number | null;
  missing_observations: number | null;
}
interface Freshness {
  source_snapshot_at: string | null;
  processed_at: string | null;
  loaded_at: string | null;
  frozen_at: string | null;
  freshness_status: "current" | "stale" | "unknown";
  freshness_policy_id: string | null;
}
interface ProvenanceRef {
  source_ids: string[];
  input_artifact_ids: string[];
  output_artifact_id: string | null;
  method_ids: string[];
  pipeline_run_id: string | null;
}
interface FieldDefinition {
  field_id: string;
  label: string;
  definition: string;
  unit: string;
  value_type: "integer" | "number" | "string" | "boolean";
  nullable: boolean;
  evidence_kind: EvidenceKind;
  aggregation: string;
  numerator_field: string | null;
  denominator_field: string | null;
  method_id: string | null;
}
interface Meta {
  contract_version: string;
  dataset_version: string;
  request_id: string;
  generated_at: string;
  requested_scope: Scope;
  effective_scope: Scope;
  availability: Availability;
  unavailable_reason: string | null;
  coverage: Coverage;
  freshness: Freshness;
  provenance: ProvenanceRef;
  field_definitions: FieldDefinition[];
  warnings: Warning[];
  pagination: { total: number; limit: number; offset: number } | null;
}
interface Envelope<T> { data: T; meta: Meta; }

interface MetricValue {
  field_id: string;
  value: number | null;
  unit: string;
  evidence_kind: EvidenceKind;
  revision_status: RevisionStatus;
  maturity_status: Maturity;
  qa_status: QAStatus;
  availability: Availability;
  missing_reason: string | null;
  source_ids: string[];
  method_id: string | null;
  reference_period: string | null;
}
interface MonthlyPoint {
  province_code: string | null;
  province_name: string | null;
  period: string;
  treatment_started: MetricValue;
  outcome_pending: MetricValue;
  pending_share_pct: MetricValue;
  population: MetricValue;
  rate_per_100k: MetricValue;
  denominator_year: number | null;
  covered_province_count: number;
  expected_province_count: number;
}
```

Key utama monthly adalah `(dataset_version, province_code, period)`; untuk nasional `province_code=null`. Tiap `field_id` pada nilai wajib memiliki tepat satu definisi cocok dalam `meta.field_definitions`. `unit` di nilai harus sama dengan registry; sumber per nilai harus dapat di-resolve pada katalog Sources. Untuk nilai turunan, sumber harus menyertakan seluruh input, bukan hanya satu publisher.

`MetricValue` berlaku untuk angka analitik. Counter struktural seperti `Coverage` tetap memiliki definisi field dan provenance tingkat respons. Status QA hanya berasal dari laporan validasi rilis, bukan disimpulkan dari request sukses atau `value != null`.

Collection kosong berbentuk `data: []`. Resource singleton yang belum tersedia berbentuk `data: null`. Singleton yang sebagian tersedia tetap objek dengan `meta.availability="partial"`; field hilang diisi `null` sesuai schema, bukan dibuang. `value=null` mewajibkan `missing_reason` non-null; angka valid nol memiliki `missing_reason=null`.

## 7. Error, partial data, dan perilaku UI

### 7.1 Schema error target

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    request_id: string;
    retryable: boolean;
    details: { field: string | null; reason: string }[];
  };
}
```

| HTTP | Code | Kapan digunakan | Tindakan UI |
| --- | --- | --- | --- |
| `200` | Bukan error | Collection kosong/fitur tercatat unavailable/partial | Empty atau partial state sesuai `meta` |
| `400` | `MALFORMED_REQUEST` | Query tidak dapat diparse | Pesan input, tidak retry otomatis |
| `404` | `RESOURCE_NOT_FOUND` | Path, versi, source ID, atau model ID tidak terdaftar | Pesan resource tidak ditemukan; jangan fallback SPA |
| `422` | `INVALID_FILTER` | Kode provinsi, enum, batas overlay, bulan, parameter tak dikenal/kombinasi salah | Tandai filter; pertahankan input |
| `429` | `RATE_LIMITED` | Jika pembatasan request diterapkan | Ikuti `Retry-After` bila ada |
| `500` | `INTERNAL_ERROR` | Bug tak terduga | Pesan umum, request ID; tanpa stack trace/path internal |
| `503` | `DATASET_NOT_READY` / `DEPENDENCY_UNAVAILABLE` | File wajib rilis terdaftar hilang, gagal QA wajib, atau dependency gagal | ErrorReloadNotice; retry jika `retryable` |

Fitur BACKLOG tidak sama dengan file wajib hilang. Capability yang sengaja unavailable boleh membalas `200` unavailable; dataset wajib yang seharusnya tersedia tetapi rusak adalah `503`. FastAPI validation handler harus dinormalisasi untuk endpoint v1; bentuk `detail` legacy tetap hanya untuk adapter legacy.

### 7.2 Kode fallback yang dipakai pada matriks widget

| Kode | Aturan tampilan |
| --- | --- |
| F1 | Skeleton berlabel “Memuat…” hanya saat request pending; `aria-busy` dan status pembaca layar |
| F2 | Nilai null → `—` + alasan; zero valid tetap `0`; jangan substitusi rerata/angka demo |
| F3 | Empty/unavailable panel, filter tetap; tombol ubah filter opsional, tidak reset otomatis |
| F4 | ErrorReloadNotice + retry request widget yang gagal; komponen sukses lain tetap tampil |
| F5 | Partial series → gap nyata tanpa interpolasi; tampilkan cakupan dan warning |
| F6 | Provinsi tanpa data → hatch/pola NoDataRegionPattern, bukan warna terendah |
| F7 | Capability unavailable/backlog → kontrol disabled dan alasan; bukan loading permanen |
| F8 | Metadata tidak diketahui → “Belum terverifikasi”; tanpa angka/tanggal/QA/sumber rekaan |
| F9 | Tombol tanpa dependency valid disabled; jelaskan alasan, jangan mengunduh file kosong seolah sukses |
| F10 | Aksi navigasi lokal mempertahankan filter dan origin; tidak memerlukan angka/API tersendiri |

Semua widget pengambil data memakai F1 dan F4 selain fallback spesifiknya. Cache lama hanya boleh ditampilkan untuk **filter dan versi dataset identik**, dengan label “data tersimpan” dan waktu data asli; respons versi/filter lain tidak boleh tersaji sebagai hasil terbaru. Batalkan/abaikan request lama ketika pengguna mengganti filter. Invalid JSON, HTML dengan HTTP 200, atau schema tidak cocok adalah error, bukan empty state.

`last_successful_fetch_at` adalah waktu fetch client; tidak boleh diberi label “data diperbarui”. Waktu error contoh dalam HTML tidak dipakai.

## 8. Freshness dan provenance

### 8.1 Tanggal dan versi

| Field | Arti |
| --- | --- |
| `period` / `reference_period` | Periode fenomena/kohort/survei yang diwakili angka |
| `source_snapshot_at` | Waktu snapshot sumber; dari ledger, tidak dari jam browser |
| `processed_at` | Waktu pipeline sukses memproduksi artefak |
| `loaded_at` | Waktu versi artefak dimuat proses backend |
| `frozen_at` | Waktu freeze rilis yang benar-benar disahkan; null bila belum ada |
| `generated_at` | Waktu respons dibuat; tidak menyiratkan data baru |
| `freshness_status` | Evaluasi berdasarkan kebijakan bernama; unknown jika SLA/frekuensi belum ditetapkan |

Timestamp memakai RFC 3339 dengan timezone; tanggal yang hanya diketahui sampai hari dipertahankan `YYYY-MM-DD`, jangan menciptakan jam. UI boleh memformat tanggal menurut locale `id-ID`; jika memakai WIB, konversi timezone secara eksplisit. Untuk respons multisumber dengan tanggal berbeda, gunakan `source_snapshot_at=null` pada envelope dan tampilkan tanggal setiap source, bukan memilih tanggal terbaru lalu menerapkannya ke semua input.

Tidak ada SLA refresh yang sudah dikonfirmasi lampiran. Kebijakan stale/freeze harus disetujui tim data; tidak menggunakan aturan “lebih dari sekian hari” tanpa dasar.

### 8.2 Lineage minimum

Setiap rilis harus menyediakan: dataset/version, source ID dan publisher, URL asli, snapshot, artefak input/output, checksum yang benar-benar dihitung, codebook version, pipeline run ID, method IDs, hasil validasi dan status provisional. Identitas artefak adalah path logis relatif terhadap produk, bukan absolute filesystem server atau signed URL rahasia.

SourceDrawer pada rate memuat SITB **dan** BPS. Drawer QA memuat laporan validasi/manifest, bukan menganggap source ledger sebagai bukti QA. Tombol “Sorot pemakaian” bekerja dari relasi `source_id → widget_ids/field_ids` yang nyata; jangan selalu menulis “Pipeline aktif (panel v1)” untuk semua sumber.

## 9. Definisi indikator dan agregasi

| Field | Tipe/unit | Definisi dan aturan agregasi | Sumber/lineage |
| --- | --- | --- | --- |
| `treatment_started` | integer ≥ 0; `patients` | Jumlah pasien mulai pengobatan TBC SO pada kohort bulan tertentu; sum provinsi hanya setelah cek key, cakupan, dan definisi | `sitb_cohort` |
| `outcome_pending` | integer ≥ 0; `patients` | Pasien kohort yang hasilnya belum tersedia pada snapshot; tidak boleh melebihi numerator kohort | `sitb_cohort` |
| `pending_share_pct` | number 0–100; `percent` | `100 × Σoutcome_pending / Σtreatment_started`, bukan mean persentase provinsi/bulan | SITB + method `pending_share` |
| `population` | number > 0; `persons` | Populasi tahun rujukan BPS setelah normalisasi unit; jangan mengasumsikan input sudah jiwa, bisa memerlukan konversi dari ribu jiwa | `bps` |
| `rate_per_100k` | number ≥ 0; `patients_per_100k_population` | `100000 × treatment_started / population` untuk bulan dan scope yang sama; bukan incidence rate atau person-time rate | SITB + BPS + method `rate` |
| `population_density` | number ≥ 0; `persons_per_km2` | Konteks provinsi/periode BPS; tidak dijumlahkan antarprovinsi | `bps` |
| `poverty_pct`, `sanitation_pct` | number 0–100; `percent` | Definisi dan denominator mengikuti indikator BPS terverifikasi, bukan asumsi semua berbasis penduduk | `bps` |
| `temperature_c` | number; `degC` | Suhu agregasi provinsi-bulan menurut metode pipeline | NASA POWER + BIG bila digunakan |
| `humidity_pct` | number 0–100; `percent` | Kelembapan relatif provinsi-bulan | NASA POWER + metode |
| `precipitation` | number ≥ 0; unit dari codebook | Nilai belum boleh diberi label mm/bulan sebelum dipastikan total bulanan vs rata-rata mm/hari | NASA POWER + metode |
| `temperature_c_z`, `humidity_z`, `precipitation_z` | number; `dimensionless` | `(nilai − normal bulan-kalender) / SD baseline`; periode baseline, metode SD, dan transformasi wajib tercatat | NASA POWER + metode normalisasi |
| `disaster_count` | integer ≥ 0; `events` | Kejadian sesuai taksonomi/deduplicasi BNPB; tidak menghitung laporan berulang sebagai kejadian baru | `bnpb` + metode |
| `count_zscore` | number; `dimensionless` | Skor dari artefak analisis; baseline dan variable harus eksplisit | `project_analysis` + SITB |
| `coefficient`, `irr`, `ci_low`, `ci_high`, `p_value` | number; unit menurut effect scale | Hanya hasil artefak model yang cocok rilis; IRR = exp(coefficient) jika coefficient berada pada log scale | Model + semua input/method |

Aturan pelengkap:

1. Denominator nol/tidak tersedia → derived value null dengan alasan, bukan `0`, Infinity, atau crash. Pasien nol dan populasi valid menghasilkan rate nol, sedangkan pending share dengan total pasien nol tidak terdefinisi.
2. Rate nasional/subset = sum pasien dibagi sum populasi provinsi yang sama; bukan rata-rata rate provinsi. Jika provinsi wajib hilang, jangan melabeli sum subset sebagai total nasional lengkap. Kontrak awal menahan headline nasional sebagai null dengan warning partial; nilai per provinsi yang tersedia tetap tampil.
3. Populasi tahunan digunakan kembali untuk tiap bulan yang cocok tahun, tidak dijumlahkan 12 kali untuk annual rate. Kontrak awal memakai rate bulanan; rate kumulatif lintas tahun tidak disediakan sebelum denominator/method disepakati.
4. Pending share per tahun memakai kohort dalam irisan rentang aktif, dengan label bulan tercakup. Tahun parsial jangan diberi label total setahun. Outcome numerator dan denominator harus memakai snapshot kohort sama.
5. Threshold `pending_share_pct ≤ 5` pada wireframe adalah **usulan operasional proyek yang belum terverifikasi dokumen metode**. Target API menyediakannya sebagai `maturity_rule`; hingga disetujui, `maturity_status="unknown"`. Jangan memakai nilai 0.05 pada field yang berskala 0–100.
6. `provisional` tidak berarti `immature`, dan `final` tidak otomatis berarti `mature`. Garis putus-putus mengikuti revision status per titik, bukan indeks array/tahun. Klaim “2024 matang” harus diperiksa per kohort.
7. Statistik kalender adalah perbandingan bulan menurut tahun, bukan bukti pola musiman yang sudah mapan. Tidak menciptakan bulan hilang dengan zero fill.
8. Kovariat sosial tidak boleh ditampilkan sebagai agregat nasional dari mean sederhana; membutuhkan denominator/metode tersendiri. Jika belum ada, national social context unavailable.
9. Lag iklim pada outcome bulan `t` merujuk iklim `t − lag_months`; sertakan kedua periodenya. Data historis sebelum filter boleh dipakai untuk lag hanya jika tersedia dan tercatat; normalisasi tidak dihitung ulang dari rentang pilihan UI.
10. Data bencana tidak lengkap ≠ nol kejadian. Nol valid memerlukan konfirmasi cakupan pencatatan. Ketidaksempurnaan rekonsiliasi ditampilkan sebagai caution.
11. PPML: jangan menyalin formula `rate ~ ...` atau IRR contoh dari wireframe. Outcome, offset populasi bila digunakan, fixed effects, standard errors, dan sample mengikuti spesifikasi peneliti. Model count dengan offset adalah pilihan yang dapat direview, bukan klaim model aktual.

## 10. Katalog endpoint target — seluruhnya PROPOSED

`V` pada tabel = `dataset_version`. Semua respons sukses memakai `Envelope<T>` kecuali CSV export dan GeoJSON yang dijelaskan khusus. Daftar ini adalah batas minimum kebutuhan wireframe, bukan endpoint yang sudah aktif. Nama endpoint dapat diganti saat review asalkan matriks widget dan OpenAPI diperbarui bersama.

| ID | Method dan path target | Parameter yang diterima | `data` / fungsi | Dependency |
| --- | --- | --- | --- | --- |
| E01 | `GET /api/v1/manifest` | `V` opsional | `ManifestData` — rilis, opsi filter, coverage, QA, capability | Master provinsi, ledger, codebook, validation, manifest rilis |
| E02 | `GET /api/v1/summary` | `V`, `start_period`, `end_period`, `period`, `province_code` | `SummaryData` atau null — KPI bulan fokus dan banner | SITB kohort + BPS + validasi |
| E03 | `GET /api/v1/tb/timeseries` | `V`, rentang, `province_code`, `overlay_province_codes`, `metric` | `TimeSeriesData` — seri primer dan overlay | SITB kohort + BPS; tidak mencampur L2 otomatis |
| E04 | `GET /api/v1/tb/calendar-pattern` | `V`, rentang, `province_code`, `metric` | `CalendarData` — per bulan-kalender dan pending agregat per tahun | E03 input atau `calendar_pattern_summary.csv` yang cocok rilis |
| E05 | `GET /api/v1/map` | `V`, `period`, `layer`, `indicator`, `metric`, `lag_months` | `MapData` atau null — nilai semua provinsi + legenda | Master provinsi + data layer + metode klasifikasi |
| E06 | `GET /api/v1/provinces/{province_code}` | `V`, rentang, `period`, `metric` | `ProvinceData` atau null — header, KPI, grafik, caution | SITB + BPS + analisis/QA opsional |
| E07 | `GET /api/v1/climate/province-monthly` | `V`, rentang, `province_code`, `indicator`, `lag_months` | `ClimateRow[]` | Panel iklim, codebook, baseline/metode NASA POWER/BIG |
| E08 | `GET /api/v1/disasters/province-monthly` | `V`, rentang, `province_code` | `DisasterRow[]` | Panel BNPB, aturan rekonsiliasi/dedup |
| E09 | `GET /api/v1/social/province-annual` | `V`, `year`, `province_code`, `indicator` opsional | `SocialRow[]` | BPS dan pemilihan reference period eksplisit |
| E10 | `GET /api/v1/methods` | `V`, `language` | `MethodsData` atau null | Dokumen metode/codebook berversi + limitations |
| E11 | `GET /api/v1/sources` | `V`, `source_id` opsional | `SourcesData` | Ledger terverifikasi dan pemetaan pemakaian |
| E12 | `GET /api/v1/changelog` | `V`, `limit`, `offset` | `ChangeEntry[]` | Riwayat perubahan rilis nyata, bukan daftar ilustratif HTML |
| E13 | `GET /api/v1/models/ppml` | `V`, `model_id` opsional | `ModelData[]` | Artefak model yang tervalidasi dan kompatibel rilis |
| E14 | `GET /api/v1/analysis/outliers` | `V`, rentang, `province_code`, `indicator`, `limit`, `offset` | `OutlierRow[]` | `national_outliers.csv` atau artefak setara yang terverifikasi |
| E15 | `GET /api/v1/exports` | `V`, `resource`, filter resource yang sama, `format` | JSON envelope atau CSV berkolom provenance | Dataset/metadata yang sama dengan layar |
| E16 | `GET /api/v1/boundaries/provinces` | `V`, `boundary_version` opsional | GeoJSON FeatureCollection dalam envelope | OPTIONAL: hanya bila memakai geometri geografis; tile-cartogram tidak perlu geometri |

`rentang` berarti `start_period` dan `end_period`. `resource` ekspor hanya salah satu `tb_timeseries`, `calendar_pattern`, `map`, `social`, `climate`, `disasters`, `outliers`, `sources`, `model_results`; filter dan capability mengikuti resource, bukan akses arbitrary file. Batas request/ukuran ekspor ditetapkan manifest sebelum rilis. Dataset default E01 dipilih oleh konfigurasi deployment; respons tetap mengembalikan version ID konkret.

### 10.1 E01 — manifest dan referensi

```typescript
interface ManifestData {
  release: {
    dataset_id: string; dataset_version: string;
    label: string; codebook_version: string;
    frozen_at: string | null; pipeline_run_id: string | null;
    revision_status: RevisionStatus;
  };
  coverage: Coverage;
  validation: {
    status: QAStatus; checked_at: string | null;
    report_artifact_id: string | null;
    duplicate_key_count: number | null;
    missing_required_count: number | null;
    checksum_status: "passed" | "failed" | "not_run";
    complete_province_count: number | null;
  };
  provinces: {
    province_code: string; province_name: string;
    region: string | null; display_order: number;
    reference_version: string;
  }[];
  source_counts: {
    active_dataset_count: number | null;
    publisher_count: number | null;
    reference_only_count: number | null;
    ledger_status: "verified" | "unverified" | "unavailable";
  };
  defaults: {
    start_period: string; end_period: string;
    focus_period: string; metric: "count" | "rate";
  };
  filter_options: {
    supported_periods: string[];
    indicators: FieldDefinition[];
    social_years: { indicator: string; years: number[] }[];
    supported_lags: number[]; languages: string[];
    max_overlay_provinces: number;
    max_page_size: number; max_export_rows: number;
  };
  capabilities: {
    id: string; status: "available" | "unavailable" | "backlog";
    reason: string | null; endpoint: string | null;
    required_source_ids: string[]; method_id: string | null;
    supported_indicators: string[];
  }[];
}
```

`coverage.month_count` adalah jumlah bulan unik, `observed_observations` adalah key unik sesudah validasi, bukan `len()` file tanpa pemeriksaan. Expected coverage berasal dari master provinsi × kalender rilis; data gagal tidak boleh mengurangi denominator sehingga QA tampak lengkap. `source_counts` null jika ledger belum terverifikasi; bukan membuat “sumber ke-7”. Header “OFFICIAL RESEARCH” adalah identitas jalur produk, bukan jaminan semua angka reported atau semua source sudah diverifikasi.

### 10.2 E02 — summary dan banner

```typescript
interface SummaryData {
  focus: MonthlyPoint;
  scope_label: string;
  available_provinces: {
    complete_count: number | null; expected_count: number;
    completeness_field_ids: string[];
    validation_report_id: string | null;
  };
  banner: {
    show_provisional: boolean;
    provisional_periods: string[];
    pending_comparison: {
      start_period: string; end_period: string;
      start_value: MetricValue; end_value: MetricValue;
      method_id: string;
    } | null;
    limitation_ids: string[];
  };
}
```

KPI pertama adalah nilai **bulan fokus**, bukan total rentang. Judul harus menyebut bulan tersebut. `complete_count` menghitung provinsi dengan semua `completeness_field_ids` wajib pada bulan fokus; bukan hanya provinsi yang memiliki satu baris. Saat scope satu provinsi, denominator adalah scope satu provinsi; coverage strip rilis tetap berlabel global. Jika definisi kelengkapan belum disepakati, angka lengkap null.

Banner tidak menyalin angka “6,5%”, “35,97%” atau klaim durasi konfirmasi dari HTML. Perbandingan hanya dirender bila kedua nilai tersedia, definisi agregasinya identik, dan periode ditampilkan. Jika tidak, tampilkan catatan provisional tanpa angka. Batas forecast ditarik dari limitation yang disetujui; jangan membuat forecast dari 24 angka wireframe.

### 10.3 E03 dan E04 — seri dan kalender

```typescript
interface TimeSeriesData {
  primary_scope: "national" | "province";
  basis: "sitb_cohort_aggregate";
  selected_metric: "count" | "rate";
  series: {
    series_id: string; label: string;
    province_code: string | null; role: "primary" | "overlay";
    points: MonthlyPoint[];
  }[];
}
interface CalendarData {
  selected_metric: "count" | "rate";
  cells: { year: number; month: number; point: MonthlyPoint }[];
  pending_by_year: {
    year: number; included_periods: string[];
    treatment_started_sum: MetricValue;
    outcome_pending_sum: MetricValue;
    pending_share_pct: MetricValue;
  }[];
  method_id: string;
}
```

`points` berurutan ascending dan memiliki satu slot tiap bulan permintaan dalam cakupan, termasuk null untuk gap. Nilai rate sudah disediakan backend memakai denominator yang benar. Chart scale, posisi titik, dan tinggi batang dihitung dari nilai API, bukan array posisi SVG. Tooltip menampilkan month, scope, value, unit, definisi, evidence kind, revision, maturity, dan source IDs.

Jika ingin menambahkan seri L2 SATUSEHAT, buat `basis` lain melalui review kontrak dan buktikan definisi indikator/snapshot. Jangan memakai L2 untuk garis nasional dan L4 untuk overlay seolah pasti satu definisi. `calendar_pattern_summary.csv` belum dilampirkan; tidak boleh mengklaim file itu mendukung filter provinsi sebelum schema/cakupannya dicek. Jika file ringkasan tidak mendukung filter, hitung melalui pipeline terverifikasi dari input kohort yang sama atau nyatakan unavailable.

### 10.4 E05 dan E16 — map, legenda, dan wilayah

```typescript
interface MapData {
  period: string;
  reference_period: string;
  layer: "tb" | "social" | "climate" | "disaster" | "consistent";
  indicator: string;
  metric: "count" | "rate" | null;
  regions: {
    province_code: string; province_name: string; region: string | null;
    value: MetricValue; class_id: string | null;
    reference_period: string | null;
  }[];
  legend: {
    method_id: string; classification: string;
    domain_scope: string; domain_period: string;
    unit: string;
    classes: {
      class_id: string; lower: number | null; upper: number | null;
      lower_inclusive: boolean; upper_inclusive: boolean;
      label: string; order: number;
    }[];
    no_data_label: string;
  };
  boundary: {
    representation: "tile_cartogram" | "geographic";
    reference_version: string;
    boundary_version: string | null;
    source_ids: string[]; disclaimer: string;
  };
}
```

- Tile-cartogram adalah representasi skematik berdasarkan master kode provinsi; geometri BIG bukan syarat untuk menggambar tile. Bila BIG dipakai untuk agregasi iklim, catat pada lineage iklim; jangan mengklaim bentuk tile adalah batas presisi BIG.
- E16 opsional: `Envelope<GeoJSON FeatureCollection>`, CRS koordinat longitude–latitude WGS84; setiap feature Polygon/MultiPolygon memiliki `properties.province_code` dan `province_name`. Join berdasarkan kode, bukan nama; boundary version tercatat dalam metadata, tidak menyisipkan nilai penelitian statis ke geometri.
- Semua region referensi hadir walau value null. Nol memiliki kelas valid; no-data `class_id=null`. Kode tidak dikenal/duplikat adalah QA error, bukan digabung sembarang.
- Klasifikasi dan batas kelas dikembalikan API berdasarkan metode yang disetujui. Fungsi `bucket(r)` dengan ambang literal pada HTML bukan standar epidemiologi dan tidak dipindahkan. Warna UI boleh ditentukan berdasarkan `order`; rentang angka berasal dari respons.
- Layer sosial harus memilih indikator spesifik: kemiskinan atau kepadatan, tidak hanya mengganti judul sambil mempertahankan nilai TB. Sanitasi dapat disediakan jika masuk scope registry. Unit mengikuti indikator; toggle count/rate tidak berlaku pada sosial/iklim/bencana dan harus disabled dengan alasan, sambil menyimpan pilihan TB pengguna.
- Iklim dan bencana tetap locked sampai capability siap. Layer `consistent` tetap BACKLOG sampai hasil/metode Global Moran/LISA disetujui. Moran/LISA saja tidak membuktikan konsistensi temporal; perlu definisi periode, pembobot spasial, signifikansi, multiple testing, dan aturan persistence sebelum memakai label tersebut.

### 10.5 E06–E09 — detail dan konteks

```typescript
interface ProvinceData {
  province_code: string; province_name: string;
  reference_version: string;
  focus: MonthlyPoint;
  trend: MonthlyPoint[];
  caution: {
    count_zscore: MetricValue;
    reason: string | null; method_id: string | null;
    analysis_status: "available" | "unavailable";
  };
}
interface ClimateRow {
  province_code: string; province_name: string;
  outcome_period: string; climate_period: string;
  indicator: string; lag_months: number;
  value: MetricValue;
  raw_value: MetricValue;
  normal_value: MetricValue;
  anomaly_value: MetricValue;
  baseline_start: string | null; baseline_end: string | null;
  aggregation_method_id: string | null;
  grid_selection_method: string | null;
}
interface DisasterRow {
  province_code: string; province_name: string; period: string;
  disaster_count: MetricValue;
  by_type: { type_code: string; type_label: string; count: MetricValue }[];
  reconciliation_status: "reconciled" | "unreconciled" | "unknown";
  recording_coverage_status: "complete" | "partial" | "unknown";
  role: "secondary_sensitivity";
  method_id: string;
}
interface SocialRow {
  province_code: string; province_name: string;
  year: number; indicator: string;
  value: MetricValue;
  reference_period: string;
  temporal_resolution: "annual" | "survey_period";
  replicated_to_months: boolean;
  population_type: "projection" | "observation" | null;
  method_id: string | null;
}
```

E07 tanpa provinsi mengembalikan seluruh baris provinsi, **bukan** mean nasional. ClimateContextPanel di Trend nasional meminta pengguna memilih provinsi; overlay iklim nasional membutuhkan metode agregasi baru dan review. E08 juga tidak menyebut total nasional tanpa kelengkapan pencatatan. E09 mengembalikan satu reference period yang dipilih secara eksplisit oleh registry/metode untuk setiap `(province, year, indicator)`; jika beberapa survei tersedia, backend tidak mengambil baris pertama secara acak.

Nilai sosial tahun lain tidak dibawa maju/mundur untuk menutup missing. Bila tim ingin kebijakan carry-forward, harus menjadi versi metode baru dengan label tahun rujukan asli. Detail mengambil E06, E07, E08, E09 secara independen; kegagalan iklim tidak menghapus KPI TB yang berhasil.

### 10.6 E10 — methods

```typescript
interface MethodsData {
  method_version: string; language: string;
  analysis_unit: string;
  pipeline_steps: { id: string; label: string; source_ids: string[] }[];
  glossary: { term_id: string; term: string; definition: string; field_ids: string[] }[];
  avoided_labels: { label: string; reason: string; preferred_label: string }[];
  rate_rule: { method_id: string; formula: string; denominator_definition: string };
  maturity_rule: {
    method_id: string | null;
    status: "approved" | "proposed" | "unavailable";
    field_id: string; operator: "lte";
    threshold_pct: number | null;
    zero_denominator_policy: string;
    explanation: string;
  };
  context_notes: {
    note_id: string; title: string; text: string;
    source_ids: string[]; method_id: string | null;
    status: "approved" | "proposed" | "backlog";
  }[];
  limitations: { id: string; text: string; applies_to: string[]; source_ids: string[] }[];
}
```

Glossary mencakup treatment initiation, treatment success, known/pending outcome, maturity, rate. Definisi treatment success tidak memberi izin menghitung success rate tanpa kategori, denominator, dan maturity yang disepakati. Empat limitations dari L7 dapat diadaptasi sebagai konten legacy beridentitas, tetapi klaim tambahan NASA/BIG/BNPB memerlukan dokumen metode, bukan sekadar menyalin HTML sebagai fakta tervalidasi.

`context_notes` harus mencakup `fact_vs_interpretation`, `climate_source_method`, `boundary_method`, `consistent_zone_method`, dan batas forecast. Tidak ada angka “38 × 24”, “912”, “0 duplicate”, atau tanggal frozen tertanam dalam Methods; angka tersebut berasal dari E01.

### 10.7 E11 dan E12 — sources dan changelog

```typescript
interface SourceRecord {
  source_id: string; publisher: string; dataset: string;
  role: "primary_outcome" | "covariate" | "boundary" | "reference_only" | "internal_artifact";
  verification_status: "verified" | "unverified";
  active_in_release: boolean;
  url: string | null;
  coverage: string; geographic_level: string;
  units: string[];
  accessed_at: string | null; snapshot_at: string | null;
  revision_status: RevisionStatus;
  quality_notes: string[];
  artifact_ids: string[];
  checksums: { artifact_id: string; algorithm: "sha256"; value: string }[];
  usage: { widget_id: string; field_ids: string[]; method_ids: string[] }[];
}
interface SourcesData {
  ledger_version: string | null;
  ledger_updated_at: string | null;
  active_dataset_count: number | null;
  publisher_count: number | null;
  sources: SourceRecord[];
}
interface ChangeEntry {
  change_id: string; occurred_at: string;
  dataset_version: string;
  category: "data" | "method" | "metadata" | "ui_label";
  summary: string;
  affected_source_ids: string[];
  affected_artifact_ids: string[];
  evidence_ref: string;
}
```

`active_dataset_count` dihitung atas source record verified, active, dan role numerik/boundary sesuai definisi registry; internal artifact dan reference-only dilaporkan terpisah. Definisi hitungan harus sama di E01, Overview, Sources, dan drawer. Sumber unverified boleh terlihat berlabel, tidak counted sebagai sumber input aktif tervalidasi.

URL harus URL asli yang diverifikasi dari ledger; `href="#"` dan domain rekaan tidak dianggap tautan sumber. Unknown source ID → `404`. Changelog bukan waktu fetch dan bukan narasi perubahan buatan; tanpa bukti riwayat kembalikan array kosong.

### 10.8 E13 dan E14 — model serta outlier

```typescript
interface ModelData {
  model_id: string; model_version: string;
  dataset_version: string; run_at: string;
  status: "validated" | "exploratory" | "failed";
  outcome_field: string; formula: string;
  offset: string | null;
  fixed_effects: string[];
  standard_error_method: string;
  cluster_unit: string | null;
  sample_scope: Scope;
  n_observations: number; n_provinces: number;
  omitted_observations: number;
  confidence_level: number;
  convergence_status: string;
  parameters: {
    term: string; exposure_unit: string;
    coefficient: number | null;
    effect_scale: "irr" | "coefficient";
    estimate: number | null;
    ci_low: number | null; ci_high: number | null;
    p_value: number | null;
    missing_reason: string | null;
  }[];
  method_ids: string[]; source_ids: string[];
  output_artifact_id: string;
  limitations: string[];
}
interface OutlierRow {
  province_code: string; province_name: string; period: string;
  indicator: string;
  observed: MetricValue;
  rate_per_100k: MetricValue;
  zscore: MetricValue;
  flag: string;
  baseline_description: string;
  method_id: string;
}
```

Model terikat rilis, sample scope, dan spesifikasi; mengganti filter provinsi UI tidak mengubah hasil estimasi model yang sudah dibuat. Tampilkan label “model pada sampel …”, jangan seolah model direfit untuk pilihan aktif. Model gagal tidak menampilkan nilai parsial sebagai hasil sah. CI dan estimate harus berada pada effect scale yang sama; untuk IRR interval diubah dari log scale jika artefak sumber memang log scale, bukan dieksponensialkan dua kali. `p_value` disimpan numerik, bukan string `<0,05`; formatting adalah tugas UI. Nilai contoh IRR dan CI pada HTML wajib dihapus.

E14 bukan ranking semua provinsi. Keputusan draf: ganti judul panel `Top provinsi — rate tertinggi` menjadi **“Observasi provinsi-bulan terflag (eksploratif)”**, tampilkan bulan pada setiap baris, dan filter rentang sesuai request. Sort default `abs(zscore)` descending, lalu `period` ascending dan kode ascending sebagai tie-breaker, setelah metode skornya tervalidasi. Batas pagination tidak mengubah universe analisis.

Jika pemilik produk menginginkan ranking, gunakan **E05 layer TB pada satu bulan fokus** lalu urutkan nilai metrik semua provinsi eligible descending dengan kode sebagai tie-breaker. Sebut “tertinggi di antara provinsi dengan data” bila cakupan tidak lengkap; jangan memakai subset outlier multi-bulan sebagai ranking.

### 10.9 E15 — unduhan

- UI mengirim versi, resource, dan filter identik dengan data yang terlihat; ekspor memakai angka presisi penuh, bukan string format lokal.
- JSON: `Envelope<T>` sama dengan resource asal, seluruh metadata tercakup.
- CSV: UTF-8, satu baris header biasa, tanpa baris komentar pendahuluan yang merusak pembacaan CSV. Bentuk long-format untuk nilai analitik: `dataset_version`, `province_code`, `province_name`, `period`, `reference_period`, `field_id`, `value`, `unit`, `source_ids`, `source_urls`, `source_snapshot_at`, `method_id`, `revision_status`, `maturity_status`, `qa_status`, `missing_reason`, `requested_filters_json`, `codebook_version`.
- Counter/parameter model dipetakan ke `field_id` dan metadata yang sesuai; source IDs/URLs multipel menggunakan representasi JSON array dalam sel yang di-escape CSV dengan benar. Snapshot yang berbeda disimpan sebagai mapping per source pada sel tersebut, bukan satu tanggal palsu.
- Missing adalah sel kosong disertai `missing_reason`, bukan angka nol. Provisional/derived/exploratory tetap tercantum; sumber dan satuan bukan hanya di label tombol.
- `Content-Type` sesuai format dan `Content-Disposition: attachment` dengan filename aman berbasis resource/rilis/periode. Error selalu JSON error §7, bukan CSV pesan error berstatus sukses.
- Tangani teks berawalan karakter formula spreadsheet secara aman tanpa mengubah makna kolom numerik. Tidak mengekspor path server, token, atau identifier pasien.
- Tombol unduh disabled sampai capability tersedia dan metadata sumber minimum lengkap. User tidak memperoleh file kosong seolah pengunduhan dataset sukses jika resource unavailable.

## 11. Matriks widget → endpoint → field → unit → source → fallback

Semua field berikut mengacu ke schema PROPOSED §6/§10. Fallback F1/F4 berlaku untuk semua widget data; kolom terakhir menyebut tambahan khusus. Notasi `.value` menunjuk nilai di `MetricValue`. `meta.provenance` dan `source_ids` selalu disertakan walau sumber ditulis ringkas. `— (UI)` berarti komponen nonnumerik yang memang tidak membutuhkan data endpoint tersendiri.

### 11.1 Global, navigasi, dan komponen bersama

| Widget ID / komponen | Endpoint dan field | Unit | Source | Filter/aksi dan fallback |
| --- | --- | --- | --- | --- |
| G01 AppHeader/OfficialResearchBadge | E01 `release.label`, capability; identitas produk statis | Label | Manifest produk | Jangan mengartikan official sebagai QA semua data; F8 |
| G02 NavTabs/BottomTabbar | — (UI): `page`, `from` | Tidak ada | Definisi navigasi desain | Lima tab utama + detail via drill-down; F10 |
| G03 GlobalFilterBar — periode/provinsi | E01 `defaults`, `filter_options.supported_periods`, `provinces[]` | Bulan, kode | Manifest + master | Semua opsi/nilai jumlah tersedia dari manifest; F7 jika gagal |
| G04 MetricToggle | E01 capability/indikator + URL `metric`; target field count/rate | pasien atau pasien/100.000 | SITB / SITB+BPS | Ubah label/tooltip/axis serentak; rate tanpa denominator F2/F7 |
| G05 ResetFilter/URL note | — (UI), E01 `defaults` | Tidak ada | Manifest + state UI | Restore nyata dari URL, reset hanya eksplisit; F10 |
| G06 ProvisionalBanner/CollapsedBanner | E02 `banner`, focus revision; E10 limitations | persen bila ada perbandingan | SITB + metode | Data provisional berdasarkan metadata; F8 tanpa perbandingan numerik |
| G07 AboutButton/SourceDrawer rilis | E01 `release`, `coverage`, `validation`, `source_counts` | tanggal, provinsi, bulan, baris, sumber | Manifest/validation/ledger | Tanggal/QA unknown F8; tidak membuat PASS |
| G08 SourceDrawer sumber | E11 `sources[]`: publisher/dataset/coverage/units/url/snapshot/usage | Sesuai unit sumber | Ledger + input terkait | Source ID dari widget; multipel untuk derived; F8 |
| G09 DataPointTooltip/source note | Respons widget: metric, period/scope, field definition + E11 sumber | Sesuai field | Sumber asli + metode | Tooltip sama dengan titik, nol valid; F2/F8 |
| G10 Reported/Derived/Exploratory/Provisional/Maturity/QA badges | `MetricValue` status terpisah; E10 maturity_rule | Label status | Source/method/validation | Unknown ditampilkan unknown; F8 |
| G11 LoadingSkeleton/UnavailablePanel/ErrorReloadNotice | Request lifecycle + `meta.availability`, warnings/error | Tidak ada | Respons/catatan client | F1–F5; waktu fetch bukan freshness dataset |

Toolbar wireframe, tombol breakpoint Desktop/Tablet/Mobile, state-switch manual, label nama komponen untuk reviewer, dan `.dev-note` adalah alat demonstrasi. Tidak memerlukan endpoint produksi dan tidak dibawa sebagai angka/hasil dashboard. State produksi dipicu request/metadata sebenarnya.

### 11.2 Overview

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| O01 CoverageStrip — provinsi | E01 `coverage.province_count` | provinsi | Master + validasi panel | Rilis penuh; F8 |
| O02 CoverageStrip — bulan/periode | E01 `coverage.month_count`, `period_min`, `period_max` | bulan/periode | Panel tervalidasi | Rilis penuh; F8 |
| O03 CoverageStrip — baris panel/version | E01 `coverage.observed_observations`, `release.dataset_version` | baris key unik | Validasi panel | Bukan length L4 mentah; F8 |
| O04 CoverageStrip — sumber aktif | E01 `source_counts.active_dataset_count` | dataset sumber | Ledger verified | Bukan hitungan publisher/placeholder; F8 |
| O05 CoverageStrip — frozen date | E01 `release.frozen_at` | tanggal/waktu | Manifest rilis | Null → belum dibekukan, bukan tanggal HTML; F8 |
| O06 KPI pasien mulai pengobatan | E02 `focus.treatment_started.value` + definisi/status | pasien | SITB kohort | Bulan fokus + provinsi/scope; F2/F3 |
| O07 KPI rate | E02 `focus.rate_per_100k.value`, `population`, `denominator_year` | pasien/100.000 penduduk | SITB+BPS+metode | Sama bulan/scope O06; denominator hilang F2 |
| O08 KPI pending share | E02 `focus.pending_share_pct.value` + maturity | persen | SITB + metode rasio | Sama kohort/snapshot; F2/F8 |
| O09 KPI provinsi tersedia | E02 `available_provinces.complete_count`, `expected_count`, definition fields | provinsi tersedia/target | Validasi menurut scope | Fokus; bukan L1 province_count; F8 jika belum diuji |
| O10 TrendPreviewCard | E03 primary `series[].points[]` | sesuai metric | SITB/BPS | Rentang + scope; sama data grafik lengkap; F3/F5 |
| O11 MapPreviewCard | E05 `regions[].value`, `legend` | sesuai metric/indikator | Sumber layer | Bulan fokus; label jumlah/rate mengikuti toggle; F3/F6 |
| O12 ActionButtonRow | — (UI): trend/map/methods/sources | Tidak ada | Navigasi desain | F10 |
| O13 FactVsInterpretationNote | E10 `context_notes[note_id=fact_vs_interpretation]` | Teks | Metode berversi | F8; jangan menyatakan hubungan iklim sebagai hasil final |

### 11.3 Trend

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| T01 NationalTrendChart/judul | E03 `primary_scope`, `basis`, `series[].points[].treatment_started` atau `rate_per_100k` | pasien/bulan atau pasien/100.000 per bulan | SITB kohort; BPS untuk rate | Nasional default atau provinsi terpilih; F3/F5 |
| T02 Segmen provisional dan legenda | E03 per-point metric `revision_status`; maturity terpisah | Label status | Snapshot/method | Tidak berdasarkan indeks ≥12; unknown F8 |
| T03 BrokenSeriesGap | E03 slot bulan dengan `.value=null` dan missing reason | unit seri | QA/cakupan sumber | Putus garis, tidak interpolasi; F5 |
| T04 ProvinceOverlaySelector | E01 `provinces`, max overlay; E03 overlay `series[]` | kode; unit sama seri utama | Master + SITB/BPS | Maks tiga provinsi; F7 bila dependency belum tersedia |
| T05 CalendarPatternChart | E04 `cells[].year`, `month`, `point` sesuai metric | pasien atau pasien/100.000 | SITB+BPS atau calendar artefak terverifikasi | Rentang aktif, jangan full-year palsu; F3/F5 |
| T06 AggregatePendingShareNote | E04 `pending_by_year[].pending_share_pct` + numerator/denominator | persen | SITB + ratio-of-sums | Tahun dan included periods eksplisit; F2 |
| T07 ClimateContextPanel | E07 `value`, `raw_value`, `normal_value`, `anomaly_value`, baseline, lag | °C/%/unit hujan atau z-score | NASA POWER + metode/BIG | Pilih provinsi; nasional tanpa metode F7; hilang F2/F3 |
| T08 DataPointTooltip/klik titik | E03 MonthlyPoint + G09; URL kode/periode untuk overlay | Sesuai metrik | Source ID setiap metric | Titik nasional tidak menuju Jawa Barat default; F10 |

### 11.4 Map

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| M01 ChoroplethMap/tile-cartogram | E05 `regions[]`; E01 master; E16 hanya jika geographic | sesuai layer | Sumber layer + master/boundary | Satu bulan fokus; F3/F6 |
| M02 MapLegend/range warna | E05 `legend.classes`, `unit`, `domain_scope`, `method_id` | sesuai layer | Metode klasifikasi + data | Kelas dari API, bukan ambang HTML; F7 jika belum disetujui |
| M03 NoDataRegionPattern | E05 `regions[].value.value=null`, missing reason | status | QA/cakupan | Nol tidak di-hatch; F6 |
| M04 MapLayerToggle — TB | E01 capabilities; E05 `layer=tb`, metric | pasien atau pasien/100.000 | SITB; BPS untuk rate | Ganti nilai + judul + tooltip; F7 |
| M05 MapLayerToggle — sosial | E05 `layer=social`, `indicator`, `reference_period` | persen atau jiwa/km² | BPS | Pilihan kemiskinan/kepadatan eksplisit; F2/F7 |
| M06 MapLayerToggle — iklim | E01 capability; E05 `layer=climate` | anomaly/unit asli atau z-score | NASA POWER/metode | Locked sampai endpoint/method siap; F7 |
| M07 MapLayerToggle — bencana | E01 capability; E05 `layer=disaster` | kejadian | BNPB/metode | Sensitivitas sekunder, caution; F7 |
| M08 MapLayerToggle — konsisten tinggi/rendah | E01 capability `consistent`, E10 note | kategori eksploratif | Metode/spatial analysis | BACKLOG; tidak klasifikasi dari rate tinggi; F7 |
| M09 TopProvinceTable → Observasi provinsi-bulan terflag | E14 `province_name`, `period`, `rate_per_100k`, `zscore`, `flag` | rate, z-score | Outlier artefak + SITB+BPS | Multi-bulan diberi label observasi, bukan ranking; F3/F8 |
| M10 BoundaryDisclaimerNote/source note | E05 `boundary.disclaimer`, source IDs; E10 boundary note | Teks | Metode/reference wilayah | Bedakan tile vs geometri; F8 |
| M11 MapClickToDetail | E05 `regions[].province_code` + period → E06 | kode/periode | Master + data scope | Semua field detail refetch; no-data tile boleh membuka detail unavailable; F10 |
| M12 Catatan warna | — (UI), E05 legend untuk data | Tidak ada | Aturan presentasi | Merah untuk error; warna TB bukan risiko; F10 |

### 11.5 Detail Provinsi

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| D01 BreadcrumbBack | — (UI): origin `from`, filter sebelumnya | Tidak ada | State navigasi | Kembali ke Trend/Map sesuai asal; F10 |
| D02 ProvinceHeaderBlock | E06 `province_code`, `province_name`, `focus.period`, revision/QA; E01 reference | kode, bulan, status | Master + SITB/validation | Tidak hanya mengganti nama sambil mempertahankan nilai Jawa Barat; F3/F8 |
| D03 Caution count Z-score | E06 `caution.count_zscore`, reason, method | z-score | Analisis outlier | Hilang/absen analisis bukan “aman”; F8 |
| D04 KPI pasien | E06 `focus.treatment_started` | pasien | SITB | Provinsi route + bulan fokus; F2 |
| D05 KPI rate | E06 `focus.rate_per_100k`, population/denominator_year | pasien/100.000 | SITB+BPS+metode | F2 denominator tidak tersedia |
| D06 KPI pending + dua status | E06 `focus.pending_share_pct`, revision/maturity; E10 rule | persen | SITB+metode | Revision dan maturity badge terpisah; F2/F8 |
| D07 ProvinceTrendChart | E06 `trend[]`, fokus titik dari `focus.period` | sesuai metric | SITB/BPS | Seluruh rentang terpilih; F3/F5 |
| D08 ProvinceClimateContext | E07 data untuk provinsi route | raw/anomaly/z-score sesuai field | NASA POWER/metode/BIG | F2/F7, tidak skeleton permanen |
| D09 ProvinceSocialContext — kepadatan | E09 `indicator=population_density`, value/reference period | jiwa/km² | BPS | Tahun/periodisasi asli; F2 |
| D10 ProvinceSocialContext — kemiskinan | E09 `indicator=poverty_pct`, value/reference period | persen | BPS | Periode survei harus terlihat; F2 |
| D11 ProvinceSocialContext — sanitasi/MissingFieldMarker | E09 `indicator=sanitation_pct`, value/missing reason | persen | BPS | Missing tetap `—`; bukan nol/rerata wilayah lain; F2 |
| D12 ProvinceDisasterNote | E08 `disaster_count`, `by_type`, reconciliation/coverage status | kejadian | BNPB+metode | Hilangkan narasi “2 kejadian” sampai data tersedia; F2/F7 |
| D13 MethodsSourcesLinkRow | — (UI): E10 anchor terkait dan E11 source IDs | Tidak ada | Kontrak navigasi/metode | Anchor ke metode outcome, iklim, BPS/BNPB; F9/F10 |

### 11.6 Methods

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| H01 Unit analisis & coverage | E10 `analysis_unit`; E01 coverage, validation duplicate count | provinsi × bulan; baris; duplikat | Manifest/validation | Rilis, bukan filter data; F8 |
| H02 Pipeline/frozen release | E10 `pipeline_steps`; E01 `release.frozen_at`, version | langkah, tanggal | Manifest/metode | Raw→processed→panel sesuai pipeline nyata; F8 |
| H03 DefinitionGlossaryList | E10 `glossary[]`, field definitions | Teks | Codebook/metode | Bahasa/versi; F3/F8 |
| H04 AvoidedLabelsNote | E10 `avoided_labels[]` | Teks | Metode produk | Hindari label insidensi/seluruh kasus/kasus baru yang salah; F8 |
| H05 RateCalculationExplainer | E10 `rate_rule` | pasien/100.000 | SITB+BPS+metode | Formula dan denominator identik dengan API; F8 |
| H06 MaturityRuleExplainer | E10 `maturity_rule` threshold/operator/status | persen | Metode disetujui | Ambang proposed tidak diberlakukan sebagai final; F8 |
| H07 ClimateSourceMethodNote | E10 context note `climate_source_method` | Teks | Metode NASA POWER | Nearest grid/reanalysis diverifikasi dahulu; F8 |
| H08 BoundaryMethodNote | E10 context note `boundary_method` | Teks | BIG/metode | Tidak menyamakan cartogram dengan batas resmi; F8 |
| H09 ConsistentZoneMethodNote | E10 `consistent_zone_method`; E01 capability | Teks/status | Rencana analisis spatial | BACKLOG S2-DAM-01/02; F7 |
| H10 GeneralLimitationsList | E10 `limitations[]`; legacy L7 `.limitations` melalui adapter | Teks | Metadata/metode | Bukan route `/api/metadata.limitations`; F3/F8 |
| H11 ModelUncertaintyBlock | E13 model metadata + `parameters[].estimate`, CI, effect scale | IRR/coefficient sesuai model | Artefak PPML/input resmi | Tidak ada contoh numerik di production; model belum ada F7; gagal F4 |

### 11.7 Sources

| Widget ID / komponen | Endpoint dan field | Unit | Source | Scope dan fallback |
| --- | --- | --- | --- | --- |
| S01 SourceSummaryBar | E11 `active_dataset_count`, `publisher_count`, `ledger_updated_at` | dataset/publisher/tanggal | Ledger | Rilis; angka tujuh dan tanggal HTML dihapus; F8 |
| S02 SourceCard — publisher/dataset/status | E11 `sources[].publisher`, `dataset`, verification/revision/role | Teks/status | Ledger | Tidak mengklaim unverified official data siap pakai; F8 |
| S03 SourceCard — cakupan/satuan | E11 `coverage`, `geographic_level`, `units` | sesuai data | Ledger/codebook | F8 |
| S04 SourceCard — tautan/akses/snapshot | E11 `url`, `accessed_at`, `snapshot_at` | URL/tanggal | Ledger | URL valid asli; null nonclickable; F8/F9 |
| S05 SourceCard — quality note | E11 `quality_notes`, revision | Teks | Audit sumber/metode | Provisional tidak otomatis immature; F8 |
| S06 SourceCard — Sorot pemakaian | E11 `usage[].widget_id`, field IDs | relasi pemakaian | Lineage rilis | WHO reference tidak disorot sebagai numerator; F9 bila relasi belum ada |
| S07 SourceCard — Detail sumber | E11 source record → G08 drawer | Sesuai source | Ledger | F8/F10 |
| S08 ChangeLogList | E12 entries dan occurred_at | tanggal/riwayat | Riwayat rilis | Tidak menyalin tiga event ilustratif; F3 |
| S09 DownloadMetadataNote | E15 capability + registry/codebook/source IDs | metadata ekspor | Rilis + provenance | Metadata ikut file; F8/F9 |
| S10 DownloadButton | E15 request resource/filter/version/format | file CSV/JSON | Data dan lineage sama layar | Disabled saat belum siap; F9, gagal F4 |

## 12. State contract untuk keenam halaman

| Halaman | Loading | Unavailable/empty | Partial | Error |
| --- | --- | --- | --- | --- |
| Overview | Skeleton coverage/KPI/preview per request | Summary tak tersedia, filter dipertahankan | Coverage rilis boleh ada, KPI missing null, preview sukses tetap tampil | Gagal summary tidak menutupi navigasi/metode yang sudah tersedia |
| Trend | Skeleton grafik/overlay | Tidak ada observasi untuk scope | Gap monthly, overlay berhasil tetap tampil; iklim unavailable terpisah | Retry seri gagal; jangan tampilkan array demo |
| Map | Skeleton peta saat fetch | Layer/periode unavailable dengan alasan | Provinsi missing di-hatch; legend dan coverage eksplisit | Error layer/data atau geometry jika dipakai; no-data bukan error |
| Detail | Skeleton header/KPI/konteks terpisah | Provinsi valid tanpa observasi | TB sukses, sosial/iklim/bencana missing masing-masing | Retry widget gagal, tidak salah menampilkan provinsi sebelumnya |
| Methods | Skeleton metadata | Versi/bahasa tidak tersedia | Glosarium tersedia, model BACKLOG tidak menjadi error seluruh page | Retry metadata; konten cache sama versi berlabel |
| Sources | Skeleton cards | Ledger versi tidak tersedia | Entry sumber unverified terlihat dengan status; count verified tidak dibuat | Retry ledger; tombol unduh disabled jika metadata wajib gagal |

Aturan aksesibilitas: status bukan hanya warna, tooltip dapat diakses keyboard/fokus, hatch memiliki label teks, dan tombol disabled menjelaskan alasan. Pesan error tidak mengungkap stack trace, file server, atau informasi rahasia.

## 13. Koreksi eksplisit terhadap wireframe sebelum production

| Temuan desain | Risiko bila dipindahkan langsung | Keputusan kontrak |
| --- | --- | --- |
| Angka KPI, count/rate arrays, cal bars, SVG polyline, detail card statis | Angka contoh menjadi klaim epidemiologi | Seluruhnya memakai E02–E09; koordinat chart dihitung dari API |
| Overview selalu Desember, Map tabel menyebut Oktober, filter rentang panjang | Pengguna tidak tahu bulan yang dibandingkan | Satu focus period eksplisit dari state/manifest; diteruskan saat drill-down |
| `openProvinceDetail` hanya mengganti nama/kode | Angka Jawa Barat tampak sebagai angka provinsi lain | Semua KPI/grafik/konteks refetch keyed by provinsi + versi + periode |
| Social layer hanya mengubah label | Peta TB diberi label kemiskinan | Nilai, unit, source, legenda diganti lewat E05 |
| TOP_PROVINCES berisi bulan berbeda dan sampel outlier | Ranking menyesatkan | Rename panel ke observasi terflag; ranking hanya data all-province pada bulan sama |
| `bucket(r)` memakai batas literal tanpa metode | Warna dianggap kategori risiko baku | Boundary kelas berversi dari API; bukan penilaian risiko |
| Kode/nama provinsi dalam array manual | Salah pemetaan wilayah/pemekaran | Master provinsi berversi; verifikasi pasangan kode terutama pemekaran Papua, jangan menganggap array desain otoritatif |
| “7 sumber”, `pending7`, gap “4/7” | Denominator sumber tidak berdasar | Hitung verified ledger; dataset berbeda dari publisher; placeholder tidak dihitung |
| Snapshot/frozen/QA PASS/changelog tanggal literal | Provenance palsu | Manifest, laporan validasi, dan changelog aktual; unknown jika belum ada |
| “2024 matang” dan “2025 provisional” dari indeks array | Revision dan maturity tercampur | Dua status terpisah per observasi/metode |
| Banner menyebut rata-rata pending; Trend rasio sum | Angka berlabel sama dihitung berbeda | Semua aggregate pending menggunakan rasio numerator/denominator yang sama |
| Detail bencana menyatakan jumlah meski endpoint absen | Data contoh dianggap temuan resmi | E08 atau unavailable |
| Climate panel skeleton pada state normal | Placeholder tampak sedang loading terus | Capability unavailable dengan alasan |
| PPML berisi contoh IRR/CI dan klaim belum dijalankan | Model contoh dianggap hasil, status bisa sudah berbeda | E13/artefak menentukan status; dokumen ini tidak memastikan ada/tidaknya run aktual |
| Drawer rate hanya membuka BPS; semua source “pipeline aktif” | Lineage numerik tidak lengkap | Daftar input SITB+BPS dan usage yang benar |
| `/api/metadata.sources`/`.limitations` ditulis seolah URL | Frontend memanggil route yang tidak ada | Legacy: GET `/api/metadata`, baca property; target E10/E11 |
| URL/filter dalam desain hanya label | Navigasi tidak konsisten | State serialisasi/parsing URL dan return path diuji |

## 14. Contoh request dan contoh respons tanpa angka penelitian rekaan

Request ini menggunakan kode/periode sebagai **contoh parameter**, bukan default production dan bukan endpoint yang sudah ada:

```http
GET /api/v1/manifest
GET /api/v1/tb/timeseries?dataset_version=release-example&start_period=2024-01&end_period=2025-12&metric=rate&overlay_province_codes=32&overlay_province_codes=35
GET /api/v1/provinces/32?dataset_version=release-example&start_period=2024-01&end_period=2025-12&period=2025-10&metric=count
GET /api/v1/map?dataset_version=release-example&period=2025-10&layer=social&indicator=poverty_pct
GET /api/v1/sources?dataset_version=release-example&source_id=sitb_cohort
```

`release-example` adalah placeholder dokumentasi yang harus diganti version ID dari manifest. Satu objek nilai unavailable yang sah untuk schema MetricValue (fixture bentuk, bukan observasi):

```json
{
  "field_id": "rate_per_100k",
  "value": null,
  "unit": "patients_per_100k_population",
  "evidence_kind": "derived",
  "revision_status": "unknown",
  "maturity_status": "not_applicable",
  "qa_status": "not_run",
  "availability": "unavailable",
  "missing_reason": "POPULATION_UNAVAILABLE",
  "source_ids": ["sitb_cohort", "bps"],
  "method_id": null,
  "reference_period": null
}
```

Contoh error target:

```json
{
  "error": {
    "code": "INVALID_FILTER",
    "message": "Periode awal tidak boleh melewati periode akhir.",
    "request_id": "example-request-id",
    "retryable": false,
    "details": [
      {"field": "start_period", "reason": "AFTER_END_PERIOD"}
    ]
  }
}
```

Contoh full-response untuk endpoint sukses harus dihasilkan dari fixture test terpisah atau dataset resmi yang telah lolos validasi, bukan disalin dari angka HTML. Nilai contoh dokumentasi tidak menjadi fallback.

## 15. Gap, prioritas, dan keputusan yang perlu review

### 15.1 Urutan kerja yang diusulkan

| Prioritas | Pekerjaan | Bukti penyelesaian |
| --- | --- | --- |
| P0 | Baca header CSV, codebook, ledger, validation, manifest/hasil analisis yang disebut desain | Registry alias/unit/provenance terverifikasi; unknown dicatat |
| P0 | Sepakati namespace v1, schema, filter, fokus bulan, dan denominator | OpenAPI/response schema + review frontend/backend/data |
| P0 | E01/E10/E11 metadata, opsi, QA, metode, sumber | Tidak ada jumlah sumber/tanggal/QA literal; source usage terhubung |
| P0 | E02/E03/E04/E06/E09 outcome/rate/pending/sosial | Uji agregasi, null/zero, filter, snapshot, dan cakupan |
| P0 | E05 tile map + TB/sosial dan state capability | Kode wilayah benar; legenda dari metode; no-data terpisah |
| P0 | Error normalisasi, API vs SPA, dan konsistensi rilis/cache | Test HTTP/MIME, versi, error/partial, request race |
| P1 | E07/E08 iklim/bencana | Endpoint dan metode terverifikasi; placeholder baru dibuka setelah siap |
| P1 | E14 outlier dan E13 PPML | Hasil nyata terikat rilis, metode/CI/scope benar; bila belum ada tetap unavailable |
| P1 | E12 changelog dan E15 unduhan | Histori nyata; file memuat metadata/filters/sumber |
| BACKLOG | Layer konsisten tinggi/rendah; E16 geographic opsional | Review spatial method dan boundary; jangan aktifkan dengan nilai rekaan |

Prioritas ini usulan dokumen, bukan penugasan baru atau perubahan sprint yang sudah disetujui. Task S2-ERI-02 menghasilkan spesifikasi dan gap; implementasi semua endpoint bukan otomatis bagian task dokumentasi.

### 15.2 Daftar keputusan terbuka

| ID | Keputusan/verifikasi yang belum tersedia | Default aman draf |
| --- | --- | --- |
| Q01 | Nama kolom asli treatment/pending/populasi/BPS/iklim | Canonical field PROPOSED; jangan publish angka sampai mapping benar |
| Q02 | Version ID, freeze, pipeline run, checksum, QA panel nyata | Null/unknown, bukan tanggal/statistik HTML |
| Q03 | Apakah nasional dihitung dari L4 atau L2 | Pilih agregat kohort L4 untuk konsistensi halaman; L2 terpisah sampai kesetaraan dibuktikan |
| Q04 | Persetujuan threshold kematangan dan mandatory fields untuk complete province | Rule status proposed; maturity unknown; complete_count null bila belum ada rule |
| Q05 | Definisi population denominator, unit dan survey period BPS | Jangan convert/replicate/carry-forward berdasarkan dugaan |
| Q06 | Jumlah sumber dan peran WHO/Profil/SATUSEHAT dalam ledger | Jangan mematok tujuh; active count dari verified roles |
| Q07 | Metode normal iklim, z-score, unit hujan, nearest grid, lag | Capability unavailable sampai codebook/metode tersedia |
| Q08 | Rekonsiliasi, coverage, jenis dan dedup bencana | Angka nol tidak diasumsikan; caution/unavailable |
| Q09 | Outlier sample vs ranking dan baseline z-score | Panel observasi terflag; bukan ranking |
| Q10 | Artefak PPML cocok rilis dan spesifikasi count/rate/offset/CI | Jangan tampilkan contoh; status berdasarkan registry model |
| Q11 | Metode batas kelas peta dan definisi “konsisten” | Metode wajib sebelum aktif; consistent BACKLOG |
| Q12 | SLA freshness, kebijakan refresh proses/cache | Unknown; jangan menyebut live/current tanpa bukti |

Pemilik review berdasarkan peran: backend menyetujui route/schema/error; frontend menyetujui binding/widget/state; data steward memverifikasi ledger/codebook/QA; penanggung jawab metode menyetujui rate, maturity, climate, outlier, dan model. Tidak ada persetujuan peran yang diasumsikan sudah diberikan.

## 16. Acceptance checklist dan contract tests

### 16.1 Selesai untuk deliverable dokumentasi S2-ERI-02

- [ ] Keenam halaman dan global/shared components memiliki baris binding di §11.
- [ ] Setiap angka/widget data memiliki endpoint, field, unit, source, scope filter, dan fallback.
- [ ] EXISTING tidak tercampur dengan PROPOSED; BLOCKED-DATA/BACKLOG memiliki alasan dan dependency.
- [ ] Semua alias source column diverifikasi, atau diberi blocker eksplisit yang disepakati reviewer.
- [ ] Endpoint/filter/schema target dan makna monthly focus disepakati frontend-backend.
- [ ] Maturity/provisional/QA/freshness/source count dibedakan dan aturan ditinjau tim data/metode.
- [ ] Perubahan desain ranking, source count, placeholder model, dan status metadata disetujui.
- [ ] Review backend, frontend, data, dan metode tercatat sebelum status diubah menjadi APPROVED.

### 16.2 Selesai untuk acceptance implementasi “tidak ada angka hardcoded”

Membuat Markdown saja tidak membuktikan bundle UI bebas hardcoded. Saat integrasi selesai, bukti berikut diperlukan:

- [ ] Audit literal HTML/JS menunjukkan COUNT_VAL, RATE_VAL, PROVINCES.rate, TOP_PROVINCES, CAL_BARS data, fixed KPI/SVG-data, snapshot/changelog/model contoh tidak terpakai produksi.
- [ ] Seluruh nilai, judul periode, sumber, unit, dan tooltip dapat ditelusuri ke response/metadata versi sama.
- [ ] Request dan respons endpoint sesuai schema OpenAPI; parameter benar-benar diterapkan.
- [ ] Semua source IDs dan method IDs yang dirujuk nilai dapat di-resolve.
- [ ] Empty/null/zero/partial/error/backlog teruji pada keenam halaman.
- [ ] Tidak ada impor data atau forecast/skor risiko sintetis dari folder demo.
- [ ] Download memiliki scope/filter/version/metadata sama dengan layar.

### 16.3 Skenario uji minimum

Angka pada contoh uji di bawah adalah fixture matematika, bukan data TB Indonesia.

| Test ID | Skenario | Expected |
| --- | --- | --- |
| C01 | Pasien valid nol, populasi positif | Count/rate `0`, tidak dianggap missing |
| C02 | Populasi null atau nol | Count tetap tersedia; rate null + reason |
| C03 | Total pasien nol pada pending share | Rasio null, maturity unknown, tidak divide by zero |
| C04 | Dua kohort: pending/total `1/10` dan `1/90` | Pending agregat `2%`, bukan mean `5,56%` |
| C05 | Dua provinsi: pasien/populasi `10/1000` dan `20/10000` | Rate agregat `30/11000 × 100000`, bukan mean rate provinsi |
| C06 | Satu provinsi wajib hilang dari nasional | Headline nasional unavailable/partial; tidak sum subset sebagai nasional lengkap |
| C07 | Satu bulan hilang di tengah seri | Slot null dan gap grafik; tidak interpolasi/zero fill |
| C08 | Filter provinsi berganti saat request lama belum selesai | Tidak ada angka provinsi lama di header provinsi baru |
| C09 | Detail dibuka dari Map/overlay Trend | Kode/bulan benar, seluruh KPI refetch, kembali ke asal dengan filter tetap |
| C10 | Titik nasional diklik | Tidak membuka detail provinsi default arbitrer |
| C11 | Social layer dipilih | Nilai, unit, source, legend dan tahun berubah; count/rate nonaktif |
| C12 | Provinsi dengan nilai `0` vs null di peta | Warna data valid vs hatch, dua label berbeda |
| C13 | Filter bulan invalid, kode tak dikenal, parameter tak dikenal, overlay >3 | `422` terstruktur; parameter tidak diabaikan |
| C14 | Periode valid di luar cakupan vs request gagal | `200` unavailable vs HTTP error, UI berbeda |
| C15 | Boundary/classification/source unresolved | Tidak menampilkan geometri/kelas/sumber rekaan; capability/metadata warning |
| C16 | Provisional tetapi pending rendah; final tetapi pending tinggi | Revision dan maturity tetap independen; threshold hanya approved |
| C17 | Ambang maturity approved tepat pada batas, di atasnya, dan value null | Operator `lte` benar; null → unknown |
| C18 | Rilis/ledger/QA belum memiliki freeze/checksum | Tidak ada frozen date, PASS atau jumlah sumber tujuh yang dibuat |
| C19 | API tak dikenal ditangani SPA atau HTML 200 | Client menolak non-JSON; target server `/api/*` harus `404` JSON |
| C20 | Outlier lintas bulan | Label observasi terflag, bukan ranking satu bulan; periode setiap baris terlihat |
| C21 | Model unavailable/failed/beda dataset_version | Tidak ada IRR/CI contoh; status dan mismatch terlihat |
| C22 | Rate dan pending saat ekspor | Presisi penuh, unit/source/metode/provisional/filters disertakan |
| C23 | Metadata response baru tetapi snapshot lama | UI membedakan generated/fetch time dari update sumber |
| C24 | E07/E08 unavailable sementara E06 sukses | Detail TB tetap dapat dipakai; context placeholder berhenti loading |
| C25 | Tahun sosial/lag climate tidak tersedia | Null/disabled + reason; tidak memakai tahun/lag lain diam-diam |
| C26 | Periode parsial tahun untuk calendar pending | Rasio hanya included periods, label bukan total setahun |
| C27 | Source dataset vs publisher vs reference-only | Count konsisten lintas E01/E11/Overview/drawer; tidak menghitung placeholder |
| C28 | CSV berganti setelah proses backend start | `loaded_at`/version jelas; tidak mengklaim automatic live refresh |
| C29 | Dua endpoint dalam satu layar mengembalikan version berbeda | UI menolak gabungan; pin/fetch ulang versi sama |
| C30 | Layout mobile/desktop dan keyboard | Data dan filter sama; tooltip/status/fallback tetap dapat diakses |

## 17. Batas kesimpulan draf

Draf ini telah memetakan seluruh bagian page dan shared components yang terdapat pada lampiran desain ke kontrak target serta gap implementasinya. Audit route EXISTING didasarkan pada pembacaan `main.py`; tidak ada klaim bahwa dataset, unit CSV, tanggal rilis, source ledger, validasi, hasil PPML, atau endpoint target telah diuji langsung.

Langkah berikutnya adalah menyelesaikan verifikasi artefak pada §4/§15, menyepakati keputusan terbuka, kemudian mengimplementasikan dan menguji binding sesuai §16. Draf ini tidak mengubah `main.py`, HTML, data resmi, atau repository.
