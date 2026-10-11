import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { valueState, COLORS, SEQUENTIAL_COLORS } from '../src/theme.js';
import { mapRecords } from '../src/data.js';

test('zero, missing, invalid and explicitly inapplicable stay distinct', () => {
  assert.equal(valueState(0).kind, 'zero');
  for (const value of [null, undefined, NaN, Infinity]) assert.equal(valueState(value).kind, 'missing');
  assert.equal(valueState(null, { invalid: true }).kind, 'invalid');
  assert.equal(valueState(null, { applicable: false }).short, 'N/A');
  assert.notEqual(valueState(null).short, 'N/A');
});

test('masked poverty values retain invalid status on maps', () => {
  const data = JSON.parse(readFileSync(new URL('../public/data/dashboard-snapshot.json', import.meta.url)));
  const issue = data.meta.invalid_fields[0];
  const records = mapRecords(data, { period: issue.period }, 'poverty');
  assert.equal(records.find((r) => r.code === issue.province_code).state.kind, 'invalid');
  assert.equal(records.find((r) => r.code === issue.province_code).value, null);
});

function luminance(hex) {
  const channels = hex.slice(1).match(/../g).map((part) => parseInt(part, 16) / 255).map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
test('body and secondary text meet AA contrast on their actual surfaces', () => {
  const calendarPairs = SEQUENTIAL_COLORS.map((color, i) => [i >= 3 ? '#FFFFFF' : COLORS.ink, color]);
  for (const [text, background] of [[COLORS.ink, COLORS.mist], [COLORS.ink, COLORS.ice], [COLORS.ink, COLORS.cyan], [COLORS.muted, COLORS.mist], [COLORS.muted, '#FFFFFF'], ['#304F60', COLORS.ice], ['#FFFFFF', COLORS.indigo], [COLORS.teal, '#FFFFFF'], ...calendarPairs]) {
    const values = [luminance(text), luminance(background)].sort((a, b) => b - a);
    assert.ok((values[0] + 0.05) / (values[1] + 0.05) >= 4.5, `${text} on ${background}`);
  }
});
