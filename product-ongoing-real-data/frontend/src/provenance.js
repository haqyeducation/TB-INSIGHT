import { monthLabel, titleCase } from './data.js';

export function sourceDate(value) {
  if (!value || !Number.isFinite(Date.parse(value))) return 'Belum tercatat';
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Jakarta' }).format(new Date(value)) + ' WIB';
}

export function contextFor(data, filters, indicator) {
  const aliases = { tb: filters.metric === 'rate' ? 'rate' : 'count', trend: filters.metric === 'rate' ? 'rate' : 'count', poverty: 'social', sanitation: 'social', density: 'social', rain: 'climate', temperature: 'climate', climate_trend: 'climate' };
  const ids = indicator === 'summary' ? ['count', 'rate', 'pending'] : [aliases[indicator] || indicator];
  const definitions = (data?.meta.field_definitions || []).filter((r) => ids.includes(r.id));
  const sourceIds = [...new Set(definitions.flatMap((r) => r.source_ids))];
  const sources = (data?.meta.sources || []).filter((r) => sourceIds.includes(r.dataset_id));
  const historic = indicator === 'trend' || indicator === 'climate_trend';
  const periods = data?.meta.spatial_periods || data?.meta.periods || [];
  const period = indicator === 'persistence'
    ? `${monthLabel(periods[0])}–${monthLabel(periods.at(-1))} · seluruh periode lampiran`
    : historic ? `${monthLabel(filters.start)}–${monthLabel(filters.end)}` : monthLabel(filters.period);
  const scope = filters.province ? titleCase(data?.meta.provinces.find((p) => p.code === filters.province)?.name) : 'Indonesia';
  let unit = definitions.map((r) => r.unit).join('; ');
  if (['poverty', 'sanitation'].includes(indicator)) unit = '%';
  if (indicator === 'density') unit = 'jiwa/km²';
  if (indicator === 'rain') unit = 'mm';
  if (indicator === 'temperature') unit = '°C';
  const rows = (data?.rows || []).filter((r) => r.period === filters.period && (!filters.province || r.province_code === filters.province));
  const references = [...new Set(rows.flatMap((r) => indicator === 'poverty' ? [r.poverty_reference_period]
    : indicator === 'sanitation' ? [r.sanitation_reference_period] : indicator === 'density' ? [r.population_reference_date]
      : indicator === 'social' ? [r.population_reference_date, r.poverty_reference_period, r.sanitation_reference_period] : []).filter(Boolean))];
  return { definitions, sources, sourceIds, scope, period, unit, references,
    provisional: ids.some((id) => ['count', 'rate', 'pending', 'outcomes'].includes(id)) && (historic ? rows.some((r) => r.revision_status === 'provisional') || (data?.rows || []).some((r) => r.period >= filters.start && r.period <= filters.end && r.revision_status === 'provisional' && (!filters.province || r.province_code === filters.province)) : rows.some((r) => r.revision_status === 'provisional')) };
}
