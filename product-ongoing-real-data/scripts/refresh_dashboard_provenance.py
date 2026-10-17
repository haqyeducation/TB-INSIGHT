"""Refresh display provenance without changing the cohort or spatial results."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from dashboard_provenance import enrich_metadata

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    target = ROOT / 'frontend/public/data/dashboard-snapshot.json'
    payload = json.loads(target.read_text(encoding='utf-8-sig'))
    for record in payload['meta']['input_files']:
        path = ROOT / record['name']
        if not path.exists():
            # The original snapshot records basenames, so resolve the known input directories.
            matches = list((ROOT / 'data/processed').glob(record['name'])) + list((ROOT / 'data/raw/big').glob(record['name']))
            if len(matches) != 1:
                raise ValueError('Cannot resolve snapshot input: ' + record['name'])
            path = matches[0]
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Input changed; rebuild the dashboard snapshot first: ' + record['name'])
    with (ROOT / 'data/processed/project_source_ledger.csv').open(encoding='utf-8-sig', newline='') as stream:
        sources = list(csv.DictReader(stream))
    payload['meta'].update(enrich_metadata(ROOT, sources, payload['rows'], payload['meta']['artifacts']))
    payload['meta']['provenance_prepared_at'] = datetime.now(timezone.utc).isoformat()
    payload['meta']['spatial_periods'] = sorted({r['period'] for r in payload['spatial'].get('hotspot_monthly_lisa_R', [])})
    payload['meta']['spatial_methods'] = payload['spatial'].get('hotspot_persistence_validation_R', {})
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')
    temporary.replace(target)
    print(json.dumps({'sources': len(sources), 'fields': len(payload['meta']['field_definitions']), 'cohort_rows': len(payload['rows']), 'data_values': 'unchanged'}))
