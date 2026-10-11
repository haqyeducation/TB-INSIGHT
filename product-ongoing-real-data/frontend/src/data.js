import { SEQUENTIAL_COLORS, DIVERGING_COLORS, valueState } from './theme.js';
export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
export const format = (value, digits = 0) => value == null || !Number.isFinite(Number(value)) ? '—' : new Intl.NumberFormat('id-ID', { maximumFractionDigits: digits }).format(value);
export const monthLabel = (period) => period ? `${MONTHS[Number(period.slice(5)) - 1]} ${period.slice(0, 4)}` : '—';
export const titleCase = (text = '') => text.toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()).replace('Dki', 'DKI').replace('Di Yogyakarta', 'DI Yogyakarta');
export const sumValid = (rows, field) => rows.length && rows.every((row) => row[field] != null) ? rows.reduce((sum, row) => sum + row[field], 0) : null;

export function aggregate(rows, expected) {
  const count = sumValid(rows, 'treatment_started');
  const population = sumValid(rows, 'population');
  const pending = sumValid(rows, 'belum_ada_hasil');
  const complete = rows.length === expected && count != null;
  return {
    count: complete ? count : null,
    population: complete ? population : null,
    rate: complete && population > 0 ? count / population * 100000 : null,
    pending: complete && count > 0 && pending != null ? pending / count * 100 : null,
    available: rows.length, expected, partial: !complete,
  };
}

export function seriesFor(data, filters, province = filters.province) {
  return data.meta.periods.filter((period) => period >= filters.start && period <= filters.end).map((period) => {
    const rows = data.rows.filter((row) => row.period === period && (!province || row.province_code === province));
    const values = aggregate(rows, province ? 1 : data.meta.provinces.length);
    return { period, label: monthLabel(period), value: values[filters.metric], count: values.count,
      rate: values.rate, pending: values.pending, provisional: rows.some((r) => r.revision_status === 'provisional') };
  });
}

export function downloadRows(rows, filename, metadata, kind = 'csv') {
  if (kind === 'metadata') {
    saveFile(JSON.stringify(metadata, null, 2), filename + '-metadata.json', 'application/json');
    return;
  }
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const escape = (value) => `"${(value != null && typeof value === 'object' ? JSON.stringify(value) : String(value ?? '')).replaceAll('"', '""')}"`;
  const text = [columns.map(escape).join(','), ...rows.map((row) => columns.map((column) => escape(row[column])).join(','))].join('\r\n');
  saveFile('\ufeff' + text, filename + '.csv', 'text/csv;charset=utf-8');
}

export function saveFile(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const CATEGORIES = ['Persistent Hotspot', 'Persistent Coldspot', 'Sporadic Hotspot', 'Sporadic Coldspot', 'Mixed/Unstable', 'Not significant'];
export const CATEGORY_COLORS = ['#333C77', '#087F83', '#8891BF', '#4DD4CD', '#755992', '#D8E3E8'];
export const LISA_CATEGORIES = ['High-High', 'Low-Low', 'High-Low', 'Low-High', 'Insignificant'];
export const LISA_COLORS = ['#333C77', '#087F83', '#8891BF', '#4DD4CD', '#D8E3E8'];
export const LAYERS = {
  tb: { label: 'Pasien mulai pengobatan', unit: 'pasien', source: 'SITB kohort + BPS untuk rate', field: 'treatment_started' },
  persistence: { label: 'Persistensi hotspot · Dame', unit: 'kategori FDR', source: 'S3-DAM-01 · lampiran terpisah', categorical: true },
  lisa: { label: 'Klaster LISA bulanan · Dame', unit: 'kategori FDR', source: 'S3-DAM-01 · lampiran terpisah', categorical: true },
  rain: { label: 'Anomali curah hujan', unit: 'mm', source: 'NASA POWER · normal 1991–2020', field: 'precipitation_mm_anomaly', diverging: true },
  temperature: { label: 'Anomali suhu', unit: '°C', source: 'NASA POWER · normal 1991–2020', field: 'temperature_c_anomaly', diverging: true },
  poverty: { label: 'Kemiskinan', unit: '%', source: 'BPS · periode survei asli', field: 'poverty_pct', social: true },
  sanitation: { label: 'Akses sanitasi layak', unit: '%', source: 'BPS · periode survei asli', field: 'sanitation_access_pct', social: true },
  density: { label: 'Kepadatan penduduk', unit: 'jiwa/km²', source: 'BPS · tahun rujukan', field: 'population_density_per_km2', social: true },
  disaster: { label: 'Kejadian bencana', unit: 'kejadian', source: 'BNPB · snapshot operasional', field: 'event_record_count' },
};

export function mapRecords(data, filters, layerId) {
  const layer = LAYERS[layerId] || LAYERS.tb;
  return data.meta.provinces.map((province) => {
    const row = data.rows.find((r) => r.province_code === province.code && r.period === filters.period);
    let value = row?.[layer.field] ?? null;
    let detail = row;
    if (layerId === 'tb') value = row?.[filters.metric === 'rate' ? 'rate_per_100k' : 'treatment_started'] ?? null;
    if (layerId === 'persistence') {
      detail = data.spatial.hotspot_persistence_R?.find((r) => r.province_code === province.code);
      value = detail?.persistence_category ?? null;
    }
    if (layerId === 'lisa') {
      detail = data.spatial.hotspot_monthly_lisa_R?.find((r) => r.province_code === province.code && r.period === filters.period);
      value = detail?.label_fdr ?? null;
    }
    const invalid = value == null && !!row?.warnings?.some((warning) => warning.includes(layer.field));
    return { ...province, value, detail, state: valueState(value, { invalid }) };
  });
}

export function scaleFor(data, layerId, metric) {
  const layer = LAYERS[layerId];
  if (layer.categorical) {
    const labels = layerId === 'persistence' ? CATEGORIES : LISA_CATEGORIES;
    const colors = layerId === 'persistence' ? CATEGORY_COLORS : LISA_COLORS;
    return { categorical: true, labels, colors, color: (value) => colors[labels.indexOf(value)] || '#F1F5F7' };
  }
  const field = layerId === 'tb' ? (metric === 'rate' ? 'rate_per_100k' : 'treatment_started') : layer.field;
  const values = data.rows.map((r) => r[field]).filter((v) => v != null);
  let min = values.length ? Math.min(...values) : 0;
  let max = values.length ? Math.max(...values) : 1;
  if (layer.diverging) { max = Math.max(Math.abs(min), Math.abs(max)); min = -max; }
  const colors = layer.diverging ? DIVERGING_COLORS : SEQUENTIAL_COLORS;
  const boundaries = Array.from({ length: 6 }, (_, i) => min + (max - min) * i / 5);
  return { min, max, colors, boundaries, categorical: false,
    color: (value) => value == null ? '#F1F5F7' : colors[Math.min(4, Math.max(0, Math.floor((value - min) / (max - min || 1) * 5)))] };
}
