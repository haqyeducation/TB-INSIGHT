import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { contextFor, sourceDate } from '../src/provenance.js';

const data = JSON.parse(readFileSync(new URL('../public/data/dashboard-snapshot.json', import.meta.url)));
const filters = { start: '2024-01', end: '2025-12', period: '2025-12', province: '', metric: 'rate' };

test('rate provenance includes the patient numerator and BPS denominator', () => {
  const result = contextFor(data, filters, 'tb');
  assert.deepEqual(result.sourceIds, ['SITB_TREATMENT_OUTCOMES_PROVINCE_MONTH', 'BPS_PROVINCE_ANNUAL_COVARIATES']);
  assert.match(result.unit, /100.000/);
  assert.equal(result.provisional, true);
  assert.equal(contextFor(data, { ...filters, metric: 'count' }, 'tb').sourceIds.length, 1);
});
test('climate has NASA and BIG provenance without inheriting SITB attribution', () => {
  const result = contextFor(data, filters, 'rain');
  assert.deepEqual(result.sourceIds, ['NASA_POWER_MERRA2_MONTHLY', 'BIG_PROVINCE_BOUNDARIES']);
  assert.equal(result.unit, 'mm');
  assert.equal(result.provisional, false);
});
test('historical access dates are not inferred from processing or link checks', () => {
  for (const source of data.meta.sources) {
    assert.equal(source.accessed_at, null);
    assert.equal(sourceDate(source.accessed_at), 'Belum tercatat');
    assert.equal(source.access_status, 'not_recorded');
  }
  assert.equal(sourceDate('not-a-date'), 'Belum tercatat');
  assert.match(sourceDate('2026-08-31T23:18:17+07:00'), /WIB/);
});
test('persistence notes keep the artifact period across selected month and trend range', () => {
  const first = contextFor(data, filters, 'persistence');
  const second = contextFor(data, { ...filters, start: '2025-05', end: '2025-06', period: '2025-05' }, 'persistence');
  assert.equal(first.period, second.period);
  assert.match(first.period, /seluruh periode lampiran/);
});
test('social context exposes original survey reference rather than only the panel month', () => {
  const result = contextFor(data, { ...filters, province: '32' }, 'poverty');
  assert.equal(result.unit, '%');
  assert.ok(result.references.some((r) => r.includes('2025')));
  assert.ok(result.definitions[0].limitation.includes('bukan observasi baru'));
});
test('all definitions resolve sources and source roles distinguish internal analysis from official inputs', () => {
  for (const field of data.meta.field_definitions) {
    for (const id of field.source_ids) assert.ok(data.meta.sources.some((r) => r.dataset_id === id));
  }
  assert.equal(data.meta.sources.find((r) => r.dataset_id === 'DAME_S3_SPATIAL_ATTACHMENTS').provenance_kind, 'internal_artifact');
  assert.equal(data.meta.sources.find((r) => r.dataset_id === 'BNPB_ANNUAL_BENCHMARKS').provenance_kind, 'reference_only');
});
