"""Display metadata, with unknown historical access dates kept explicit."""
import hashlib
import json
from pathlib import Path

SITB = 'SITB_TREATMENT_OUTCOMES_PROVINCE_MONTH'
BPS = 'BPS_PROVINCE_ANNUAL_COVARIATES'
NASA = 'NASA_POWER_MERRA2_MONTHLY'
BIG = 'BIG_PROVINCE_BOUNDARIES'
BNPB = 'BNPB_OPERATIONAL_EVENTS'
ANNUAL = 'BNPB_ANNUAL_BENCHMARKS'
DAME = 'DAME_S3_SPATIAL_ATTACHMENTS'


def enrich_metadata(root, sources, rows, artifacts):
    link_file = root / 'data/reference/source_link_checks.json'
    checks = json.loads(link_file.read_text(encoding='utf-8')) if link_file.exists() else {'checks': []}
    usage = {
        SITB: (['pasien', '%'], ['Ringkasan', 'Tren', 'Peta TB', 'Profil provinsi']),
        BPS: (['jiwa', 'jiwa/km²', '%'], ['Rate per 100.000', 'Peta sosial', 'Konteks provinsi']),
        NASA: (['°C', 'mm', 'simpangan baku'], ['Peta anomali', 'Grafik iklim provinsi']),
        BIG: (['poligon provinsi'], ['Seluruh peta', 'Agregasi spasial iklim']),
        BNPB: (['kejadian'], ['Peta bencana', 'Konteks bencana provinsi']),
        ANNUAL: (['kejadian per tahun'], ['Pembanding rekonsiliasi BNPB; tidak menjadi angka bulanan']),
    }
    for source in sources:
        sid = source['dataset_id']
        units, widgets = usage.get(sid, ([], []))
        # This field is deliberately not inferred from file times or pipeline runs.
        source.update(accessed_at=None, access_status='not_recorded', units=units, usage=widgets,
                      provenance_kind='reference_only' if sid == ANNUAL else 'official_input',
                      verification_status='not_signed_off', artifact_ids=[], recorded_snapshot_at=[])
        if sid == SITB:
            source['recorded_snapshot_at'] = sorted({r['source_snapshot_at'] for r in rows if r.get('source_snapshot_at')})
            source['snapshot_explanation'] = 'Kolom snapshot_retrieved_at dicatat oleh skrip penyiapan SITB. Ini waktu pencatatan pada hasil olahan; bukan bukti waktu unduh HTML asli.'
        else:
            source['snapshot_explanation'] = 'Tanggal snapshot sumber belum tercatat pada metadata yang dapat diverifikasi.'
        source['link_checks'] = [r for r in checks['checks'] if r['source_id'] == sid]
        source['checksums'] = []
        for pattern in source.get('local_files', '').split(';'):
            for path in sorted(root.glob(pattern.strip())):
                if path.is_file():
                    relative = path.relative_to(root).as_posix()
                    source['artifact_ids'].append(relative)
                    source['checksums'].append({'artifact_id': relative, 'algorithm': 'sha256', 'value': hashlib.sha256(path.read_bytes()).hexdigest()})
    if artifacts:
        sources.append(dict(dataset_id=DAME, publisher='Dame · analisis tim TB-INSIGHT',
                            source_url='', coverage='Provinsi dan bulan sesuai isi lampiran S3',
                            role='Lampiran analisis spasial; bukan sumber pasien baru', status='Belum direkonsiliasi dengan kohort aktif',
                            local_files='data/reference/dame_s3/', limitation='Input analisis Dame belum dicocokkan dengan checksum kohort aktif. Not significant tidak berarti tidak ada pasien TB.',
                            accessed_at=None, access_status='not_recorded', recorded_snapshot_at=[],
                            snapshot_explanation='Tanggal pada nama arsip bukan bukti tanggal akses atau tanggal analisis.',
                            units=['kategori LISA/FDR', 'bulan signifikan', 'p-FDR'],
                            usage=['Peta LISA', 'Persistence', 'Hasil spasial provinsi'], provenance_kind='internal_artifact',
                            verification_status='not_signed_off', link_checks=[],
                            artifact_ids=[a['name'] for a in artifacts],
                            checksums=[{'artifact_id': a['name'], 'algorithm': 'sha256', 'value': a['sha256']} for a in artifacts]))
    definitions = [
        ('count', 'Pasien mulai pengobatan', 'pasien', [SITB], 'Jumlah pasien mulai pengobatan TBC sensitif obat pada provinsi dan bulan kohort. Nasional menjumlahkan seluruh provinsi yang lengkap.', 'Bukan insidensi, semua notifikasi, atau semua orang dengan TB.'),
        ('rate', 'Rate inisiasi pengobatan', 'pasien per 100.000 penduduk', [SITB, BPS], 'Jumlah pasien mulai pengobatan ÷ penduduk tahun rujukan × 100.000. Nasional memakai rasio total pasien terhadap total penduduk.', 'Bukan rata-rata rate provinsi. Denominator kosong atau tidak positif menghasilkan nilai tidak tersedia.'),
        ('pending', 'Outcome tertunda', '%', [SITB], 'Belum ada hasil ÷ pasien mulai pengobatan × 100. Nasional dan tahunan memakai rasio total.', 'Denominator nol menghasilkan nilai tidak tersedia; pending dan provisional berbeda dari status matang.'),
        ('outcomes', 'Komposisi outcome kohort', 'pasien', [SITB], 'Jumlah pasien pada kategori hasil pengobatan yang tercatat untuk kohort bulan fokus.', 'Komposisi bukan peluang sembuh. Belum ada klaim treatment success rate tervalidasi.'),
        ('social', 'Konteks sosial dan penduduk', 'jiwa; jiwa/km²; %', [BPS], 'Populasi dan kepadatan mengikuti tahun rujukan; kemiskinan dan sanitasi mengikuti periode survei.', 'Nilai tahunan berulang di panel bulanan bukan observasi baru. Persentase di luar 0–100 disembunyikan.'),
        ('climate', 'Anomali iklim', '°C untuk suhu; mm untuk hujan', [NASA, BIG], 'Deviasi terhadap normal bulan kalender 1991–2020, diagregasi dari grid ke wilayah provinsi sesuai metode pada baris data.', 'Reanalisis, bukan pengamatan stasiun. Wilayah kecil dapat memakai grid terdekat. Pola bersamaan tidak membuktikan sebab akibat.'),
        ('disaster', 'Kejadian bencana', 'kejadian', [BNPB], 'Hitungan kejadian operasional per provinsi dan bulan setelah pengolahan proyek.', 'Hanya konteks/sensitivitas. Snapshot belum sepenuhnya cocok dengan kompilasi tahunan. Nol tercatat bukan jaminan tidak ada kejadian.'),
        ('lisa', 'LISA bulanan', 'kategori FDR; p-FDR', [DAME, BIG], 'Kategori klaster spasial dan p-FDR dari artefak analisis Dame pada bulan fokus.', 'Lampiran terpisah, input belum direkonsiliasi. Not significant bukan tidak ada pasien; kategori deskriptif bukan diagnosis risiko.'),
        ('persistence', 'Persistence hotspot', 'kategori; bulan signifikan', [DAME, BIG], 'Ringkasan frekuensi kategori signifikan sepanjang periode yang tersedia pada artefak Dame.', 'Seluruh periode lampiran; tidak berubah dengan bulan fokus dan tidak diganti hasil rentang tren.'),
    ]
    fields = [dict(id=i, label=l, unit=u, source_ids=s, definition=d, limitation=c) for i,l,u,s,d,c in definitions]
    methods = dict(version='dashboard-methods-v1', approval_status='Untuk review metode',
                   analysis_unit='Provinsi dan bulan kohort', language='id',
                   references=['docs/project-protocol.md', 'docs/design/api-ui-contract.md'],
                   maturity_status='Belum ada aturan kematangan berversi yang disetujui untuk UI',
                   glossary=[
                       {'term': 'Provisional', 'definition': 'Data dapat direvisi. Kohort 2025 ditandai provisional sesuai protokol; kohort 2024 tidak otomatis final.'},
                       {'term': 'Outcome diketahui', 'definition': 'Pasien mulai pengobatan dikurangi pasien yang belum memiliki hasil, jika kedua komponen tersedia.'},
                       {'term': 'Treatment success', 'definition': 'Sembuh ditambah pengobatan lengkap. Rasio keberhasilan memerlukan denominator dan aturan kematangan yang disetujui.'},
                       {'term': 'Fakta dan interpretasi', 'definition': 'Angka berasal dari snapshot; penjelasan pola bersifat deskriptif dan tidak menyatakan hubungan kausal.'},
                       {'term': 'Nol dan data kosong', 'definition': 'Nol tercatat tetap nol. Nilai hilang tidak diganti nol. N/A hanya jika metadata menyatakan indikator tidak berlaku.'},
                   ],
                   open_reviews=['Kecocokan definisi dan aturan kematangan dengan penanggung jawab metode.', 'Rekonsiliasi input analisis Dame dengan kohort aktif.', 'Tanggal akses historis yang belum tercatat; tidak diisi dari waktu persiapan dashboard.', 'Persetujuan manifest freeze dan status akhir QA penelitian.'])
    return {'sources': sources, 'field_definitions': fields, 'methods': methods,
            'provenance_version': 'sources-context-v1', 'source_link_check_policy': 'Pemeriksaan tautan terpisah dari akses dataset dan tidak memperbarui nilai penelitian.'}
