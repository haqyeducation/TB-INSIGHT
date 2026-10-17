# Implementasi S3 ERI 02

Halaman Sumber, Metode, dan catatan pada visual menggunakan metadata pada snapshot alpha yang sama dengan data dashboard. Pekerjaan ini tidak mengubah nilai kohort atau hasil analisis Dame dan tidak menyatakan endpoint usulan `/api/v1/*` telah tersedia.

## Cakupan implementasi

| Kriteria | Implementasi |
| --- | --- |
| Sumber | Penerbit, URL ledger, cakupan, satuan, peran, pemakaian, berkas, checksum, dan keterbatasan. Input resmi, referensi pembanding, dan lampiran tim dibedakan. |
| Tanggal akses | Field `accessed_at` tersedia dengan nilai null dan label Belum tercatat jika tidak ada bukti. Pemeriksaan tautan memiliki waktu dan status tersendiri. |
| Satuan dan definisi outcome | Registry sembilan definisi; rate dan pending memakai rasio total. Definisi dan rumus dapat dibuka dekat visual serta pada Metode. |
| Provisional | Peringatan kohort yang relevan mengikuti bulan/rentang. Provisional, kematangan outcome, dan QA penelitian dibedakan. |
| Keterbatasan | Catatan ekologis/nonkausal, batas dua tahun, periode survei BPS, reanalisis dan grid NASA, generalisasi BIG, rekonsiliasi BNPB dan Dame, serta placeholder model/forecast. |
| Context note | Ringkasan, tren, kalender, tabel ringkasan, peta, outcome, konteks sosial, iklim, dan bencana memiliki penjelasan terkait. Tombol menampilkan hanya sumber visual pilihan dan dapat dikembalikan ke semua sumber. |
| Unduhan | Metadata memuat versi, sumber, tanggal, definisi, metode, checksum, serta status. Daftar sumber dapat diunduh sebagai CSV. |

## Audit tanggal

`snapshot_retrieved_at` pada keluaran SITB diisi oleh `scripts/prepare_sitb_province_month.py` ketika menyiapkan hasil olahan. Tanggal tersebut dipertahankan sebagai `recorded_snapshot_at` dengan penjelasan, bukan dipromosikan menjadi bukti waktu unduh HTML asli. Tanggal pembuatan arsip dan waktu perubahan berkas juga tidak menjadi tanggal akses.

`scripts/check_dashboard_source_links.py` memeriksa halaman referensi tanpa menyimpan ulang data penelitian. Catatan berisi waktu UTC, status HTTP, dan checksum sampel respons jika berhasil. Tampilan tanggal menggunakan Asia/Jakarta. Hasil pemeriksaan tautan bukan verifikasi isi dataset, tanda QA lulus, atau pengganti tanggal akses historis.

## Pemeliharaan

Jalankan dari folder produk:

```powershell
.\.venv\Scripts\python.exe scripts\check_dashboard_source_links.py
.\.venv\Scripts\python.exe scripts\refresh_dashboard_provenance.py
```

Pembaruan metadata memeriksa checksum input snapshot terlebih dahulu. Jika input berubah, siapkan ulang snapshot melalui `prepare_dashboard.py`, bukan menghubungkan metadata baru ke nilai lama. Script persiapan lengkap juga menerapkan registry provenance yang sama.

## Acuan dan review

`docs/design/api-ui-contract.md` adalah salinan DRAFT v0.1 yang diberikan pengguna; status draf dipertahankan. `docs/project-protocol.md` menjadi rujukan metode yang tersedia pada checkout. Draft S2-ADZ-01 versi 0.5 belum ditemukan pada berkas kerja yang diperiksa, sehingga persetujuan kesesuaian metode tetap memerlukan reviewer. Aturan kematangan berversi, freeze, QA penelitian, dan rekonsiliasi input Dame tidak dinyatakan telah disetujui oleh implementasi UI ini.

## Pemeriksaan

`node --test tests/*.test.js` memeriksa 18 kasus, termasuk provenance numerator/denominator, sumber iklim, tanggal unknown, periode persistence, periode survei, resolusi ID sumber, agregasi, nilai kosong, dan kontras. Build produksi menyertakan metadata yang diperbarui. Pemeriksaan browser mencakup penelusuran sumber, filter sumber, kamus indikator, unduhan metadata, serta tampilan desktop dan ponsel.
