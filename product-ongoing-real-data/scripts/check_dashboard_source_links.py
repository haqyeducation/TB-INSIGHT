"""Check reference links without replacing or refreshing the study data."""
import csv
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def check(item):
    sid, url = item
    result = {'source_id': sid, 'url': url, 'checked_at': datetime.now(timezone.utc).isoformat(), 'check_kind': 'reference_link_only'}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'TB-INSIGHT source-reference-check/1.0'}), timeout=18) as response:
            sample = response.read(524288)
            result.update(http_status=response.status, reachable=200 <= response.status < 300,
                          final_url=response.url, response_sample_sha256=hashlib.sha256(sample).hexdigest())
    except HTTPError as error:
        result.update(http_status=error.code, reachable=False, error='HTTP_ERROR')
    except Exception as error:
        result.update(http_status=None, reachable=False, error=type(error).__name__)
    return result


if __name__ == '__main__':
    with (ROOT / 'data/processed/project_source_ledger.csv').open(encoding='utf-8-sig', newline='') as stream:
        items = [(row['dataset_id'], url.strip()) for row in csv.DictReader(stream) for url in row['source_url'].split(';') if url.strip().startswith('https://')]
    with ThreadPoolExecutor(max_workers=6) as pool:
        checks = list(pool.map(check, items))
    target = ROOT / 'data/reference/source_link_checks.json'
    target.write_text(json.dumps({'policy': 'Reference link checks are not historical dataset download dates.', 'checks': checks}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checked': len(checks), 'reachable': sum(r['reachable'] for r in checks)}))
