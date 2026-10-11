import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { aggregate, mapRecords, seriesFor, scaleFor } from '../src/data.js';

const snapshot = JSON.parse(readFileSync(new URL('../public/data/dashboard-snapshot.json', import.meta.url)));
const boundaries = JSON.parse(readFileSync(new URL('../public/maps/provinces.geojson', import.meta.url)));
const filters = { province: '', start: '2024-01', end: '2025-12', period: '2025-12', metric: 'count' };

test('national rate and pending share use ratios of sums', () => {
  const result = aggregate([
    { treatment_started: 10, population: 1000, belum_ada_hasil: 1 },
    { treatment_started: 90, population: 10000, belum_ada_hasil: 1 },
  ], 2);
  assert.equal(result.pending, 2);
  assert.equal(result.rate, 100 / 11000 * 100000);
});
test('missing province does not masquerade as a complete national total', () => {
  const result = aggregate([{ treatment_started: 10, population: 1000, belum_ada_hasil: 1 }], 2);
  assert.equal(result.count, null);
  assert.equal(result.rate, null);
  assert.equal(result.partial, true);
});
test('real zero and unavailable denominator remain distinct', () => {
  assert.equal(aggregate([{ treatment_started: 0, population: 1000, belum_ada_hasil: 0 }], 1).rate, 0);
  assert.equal(aggregate([{ treatment_started: 0, population: 1000, belum_ada_hasil: 0 }], 1).pending, null);
  const result = aggregate([{ treatment_started: 10, population: null, belum_ada_hasil: 1 }], 1);
  assert.equal(result.count, 10);
  assert.equal(result.rate, null);
});
test('missing monthly observation becomes a gap', () => {
  const data = { meta: { periods: ['2024-01', '2024-02'], provinces: [{ code: '11' }] }, rows: [{ province_code: '11', period: '2024-01', treatment_started: 0, population: 1000, belum_ada_hasil: 0 }] };
  const points = seriesFor(data, { ...filters, province: '11', end: '2024-02' });
  assert.equal(points[0].value, 0);
  assert.equal(points[1].value, null);
});
test('snapshot preserves unique observations and masks invalid percentages', () => {
  assert.equal(new Set(snapshot.rows.map((r) => `${r.province_code}:${r.period}`)).size, snapshot.rows.length);
  for (const row of snapshot.rows) {
    assert.ok(row.poverty_pct == null || (row.poverty_pct >= 0 && row.poverty_pct <= 100));
    assert.equal(row.rate_per_100k, row.treatment_started / row.population * 100000);
  }
  for (const issue of snapshot.meta.invalid_fields) {
    assert.equal(snapshot.rows.find((r) => r.province_code === issue.province_code && r.period === issue.period)[issue.field], null);
  }
});
test('Papua geometry is crosswalked by province identity, not incompatible original code', () => {
  assert.equal(boundaries.features.length, snapshot.meta.provinces.length);
  const names = Object.fromEntries(snapshot.meta.provinces.map((p) => [p.code, p.name]));
  for (const feature of boundaries.features) assert.equal(feature.properties.province_name, names[feature.properties.province_code]);
  const papua = boundaries.features.find((f) => f.properties.province_name === 'PAPUA');
  assert.equal(papua.properties.province_code, '94');
  assert.equal(papua.properties.boundary_source_code, '91');
  assert.equal(new Set(boundaries.features.map((f) => f.properties.province_code)).size, snapshot.meta.provinces.length);
});
test('persistence stays a full-period result when month filter changes', () => {
  assert.deepEqual(mapRecords(snapshot, filters, 'persistence'), mapRecords(snapshot, { ...filters, period: '2024-01' }, 'persistence'));
  assert.equal(mapRecords(snapshot, filters, 'persistence').filter((r) => r.value === 'Not significant').length, 38);
});
test('monthly map and province trend follow the selected observation', () => {
  const points = seriesFor(snapshot, { ...filters, province: '32' });
  const row = snapshot.rows.find((r) => r.province_code === '32' && r.period === filters.period);
  assert.equal(points.at(-1).value, row.treatment_started);
  assert.equal(mapRecords(snapshot, filters, 'tb').find((r) => r.code === '32').value, row.treatment_started);
});
test('numeric map scale is fixed across months and null has its own color', () => {
  const scale = scaleFor(snapshot, 'rain', 'count');
  assert.equal(scale.min, -scale.max);
  assert.notEqual(scale.color(null), scale.color(0));
  assert.ok(scale.boundaries.every(Number.isFinite));
});
