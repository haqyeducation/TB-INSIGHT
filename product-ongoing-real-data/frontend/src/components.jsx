import { useEffect, useId, useRef, useState } from 'react';
import { Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertCircle, ArrowUpRight, Download, Info, Maximize2, Minimize2, RefreshCw } from 'lucide-react';
import { format, monthLabel, titleCase, seriesFor } from './data';
import { COLORS, SERIES_COLORS } from './theme';
import { useReducedMotion } from './hooks';

export function Panel({ title, eyebrow, note, action, children, className = '', expandable = false }) {
  const [expanded, setExpanded] = useState(false);
  const panelRef = useRef(null);
  const titleId = useId();
  useEffect(() => {
    if (!expanded) return;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    panelRef.current?.querySelector('.expand-button')?.focus();
    const handleKey = (event) => {
      if (event.key === 'Escape') setExpanded(false);
      if (event.key !== 'Tab') return;
      const elements = [...panelRef.current.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]')];
      const first = elements[0], last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', handleKey);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handleKey); previousFocus?.focus(); };
  }, [expanded]);
  return <section ref={panelRef} className={`panel ${className} ${expanded ? 'is-expanded' : ''}`} role={expanded ? 'dialog' : undefined} aria-modal={expanded || undefined} aria-labelledby={titleId}><div className="panel-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2 id={titleId}>{title}</h2>{note && <p>{note}</p>}</div><div className="panel-actions">{action}{expandable && <button className="button secondary expand-button" onClick={() => setExpanded(!expanded)} aria-label={`${expanded ? 'Tutup tampilan besar' : 'Perbesar visual'}: ${title}`}>{expanded ? <Minimize2 size={16}/> : <Maximize2 size={16}/>}</button>}</div></div>{children}</section>;
}
export function DataStates() {
  return <div className="data-state-key" aria-label="Arti status data"><span><b>0</b>Nol tercatat</span><span><i className="state-missing"/>Belum tersedia</span><span><i className="state-invalid"/>Belum valid</span><details><summary>Tentang N/A</summary><p>N/A hanya digunakan jika metadata sumber menyatakan indikator tidak berlaku. Data yang hilang tidak otomatis menjadi N/A.</p></details></div>;
}
export function Note({ children, warning = false }) {
  return <div className={`note ${warning ? 'warning' : ''}`}><Info size={16} aria-hidden="true"/><span>{children}</span></div>;
}
export function Missing({ title, requirement, type = 'line', selection = false }) {
  return <div className="missing-visual" role="status"><div className={`empty-plot ${type}`} aria-hidden="true"><div/><div/><div/><div/></div><div className="missing-copy"><span className="missing-icon"><AlertCircle size={24}/></span><strong>{title}</strong><p>{selection ? requirement : `Masih memerlukan data ${requirement}.`}</p><span>{selection ? 'Gunakan filter Wilayah di bagian atas.' : 'Ruang visual tersedia · nilai belum ditampilkan'}</span></div></div>;
}
export function SourceNote({ children = 'SITB kohort pengobatan · BPS untuk denominator populasi.', onMethods }) {
  return <div className="source-note"><span><Info size={13}/>{children}</span>{onMethods && <button className="text-button" onClick={onMethods}>Sumber & metode <ArrowUpRight size={13}/></button>}</div>;
}
export function Stat({ label, value, unit, note, accent = false }) {
  return <article className={`stat ${accent ? 'accent' : ''}`}><span className="stat-label">{label}</span><div className="stat-number">{value}<small>{unit}</small></div><p>{note}</p></article>;
}
export function Empty({ children, retry }) {
  return <div className="empty-state"><AlertCircle size={28}/><h3>Data belum tersedia</h3><p>{children}</p>{retry && <button className="button" onClick={retry}><RefreshCw size={15}/>Coba lagi</button>}</div>;
}
export function ExportButton({ onClick, label = 'Unduh data', disabled = false }) {
  return <div className="button-group"><button className="button secondary" onClick={() => onClick?.('csv')} disabled={disabled}><Download size={15}/>{label}</button>{label === 'Unduh data' && <button className="button secondary" onClick={() => onClick?.('metadata')} disabled={disabled} title="Unduh metadata sumber, filter, dan versi data">Metadata</button>}</div>;
}

function TrendTooltip({ active, payload, label, metric }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return <div className="trend-tooltip"><strong>{monthLabel(label)}</strong><span>{point.provisional ? 'Provisional' : 'Status revisi belum diketahui'}</span>{payload.map((entry) => {
    const detail = entry.dataKey === 'value' ? point : point[`${entry.dataKey}_detail`];
    return <div key={entry.dataKey} className="tooltip-series"><b style={{ color: entry.color }}>{entry.name}</b><strong>{format(entry.value, metric === 'rate' ? 2 : 0)} <small>{metric === 'rate' ? 'pasien / 100.000' : 'pasien'}</small></strong><p>{format(detail?.count)} pasien · rate {format(detail?.rate, 2)} /100.000</p><p>Outcome tertunda {format(detail?.pending, 1)}%</p></div>;
  })}<small>SITB kohort · BPS untuk denominator</small></div>;
}

export function TrendChart({ data, filters, overlays = [], onPoint, height = 300 }) {
  const reduced = useReducedMotion();
  const gradientId = useId().replaceAll(':', '');
  const points = seriesFor(data, filters);
  const palette = SERIES_COLORS.slice(1);
  const overlayList = overlays.filter((code) => code !== filters.province).slice(0, 3);
  overlayList.forEach((code) => {
    const overlayPoints = seriesFor(data, filters, code);
    points.forEach((point, i) => { point[code] = overlayPoints[i]?.value ?? null; point[`${code}_detail`] = overlayPoints[i]; });
  });
  if (!points.length) return <Empty>Tidak ada bulan pada rentang yang dipilih.</Empty>;
  if (points.every((point) => point.value == null)) return <Missing title="Seri bulanan belum tersedia" requirement="observasi kohort lengkap untuk wilayah, periode, dan metrik pilihan"/>;
  const scope = filters.province ? titleCase(data.meta.provinces.find((p) => p.code === filters.province)?.name) : 'Nasional';
  const provisionalStart = points.find((point) => point.provisional)?.period;
  return <div style={{ height }} className="trend-chart"><ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 300, height }}><ComposedChart data={points} margin={{ top: 24, right: 16, bottom: 4, left: 0 }} onClick={(event) => {
    const point = points.find((item) => item.period === event?.activeLabel) ?? points[event?.activeTooltipIndex];
    if (point && onPoint) onPoint(point.period);
  }}><defs><linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={COLORS.ice} stopOpacity={0.38}/><stop offset="100%" stopColor={COLORS.ice} stopOpacity={0.02}/></linearGradient></defs><CartesianGrid stroke={COLORS.border} strokeDasharray="3 5" vertical={false}/><XAxis dataKey="period" tickFormatter={monthLabel} minTickGap={30} tick={{ fontSize: 13, fill: COLORS.muted }} axisLine={false} tickLine={false}/><YAxis tickFormatter={(value) => format(value, filters.metric === 'rate' ? 1 : 0)} width={76} tick={{ fontSize: 13, fill: COLORS.muted }} axisLine={false} tickLine={false}/><Tooltip content={<TrendTooltip metric={filters.metric}/>}/>{provisionalStart && <ReferenceArea x1={provisionalStart} x2={points.at(-1).period} fill={COLORS.ice} fillOpacity={0.2} label={{ value: 'Provisional', fill: COLORS.indigo, fontSize: 12, position: 'insideTop' }}/>}<ReferenceLine x={filters.period} stroke={COLORS.teal} strokeDasharray="4 4" strokeWidth={1.5}/><Area type="linear" dataKey="value" name={scope} fill={`url(#${gradientId})`} stroke={COLORS.indigo} strokeWidth={3} dot={points.length === 1 ? { r: 5 } : false} activeDot={{ r: 6, fill: COLORS.cyan, stroke: COLORS.ink, strokeWidth: 2 }} connectNulls={false} isAnimationActive={!reduced} animationDuration={450}/>{overlayList.map((code, i) => <Line key={code} dataKey={code} type="linear" name={titleCase(data.meta.provinces.find((p) => p.code === code)?.name)} stroke={palette[i]} strokeDasharray={i === 0 ? '6 3' : i === 1 ? '2 3' : '9 3 2 3'} dot={false} strokeWidth={2.5} connectNulls={false} isAnimationActive={!reduced} animationDuration={450}/>)}<Legend iconType="line" wrapperStyle={{ fontSize: 13, paddingTop: 12 }}/></ComposedChart></ResponsiveContainer></div>;
}

export function SearchTable({ columns, rows, onRow, searchKey = 'province_name', maxHeight = 430, initialSort }) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState(initialSort || { key: columns[0].key, desc: false });
  const filtered = rows.filter((row) => String(row[searchKey] ?? '').toLowerCase().includes(search.toLowerCase()));
  const sorted = [...filtered].sort((a, b) => {
    const left = a[sort.key], right = b[sort.key];
    if (left == null) return 1;
    if (right == null) return -1;
    return (typeof left === 'number' ? left - right : String(left).localeCompare(String(right))) * (sort.desc ? -1 : 1);
  });
  const searchLabel = searchKey === 'period' ? 'Cari bulan' : 'Cari provinsi';
  return <><div className="table-tools"><input aria-label={searchLabel} placeholder={searchLabel + '…'} value={search} onChange={(e) => setSearch(e.target.value)}/><span>{filtered.length} baris · klik judul kolom untuk mengurutkan</span></div><div className="table-scroll" style={{ maxHeight }}><table><thead><tr>{columns.map((column) => <th key={column.key} aria-sort={sort.key === column.key ? (sort.desc ? 'descending' : 'ascending') : 'none'}><button onClick={() => setSort({ key: column.key, desc: sort.key === column.key ? !sort.desc : false })}>{column.label}{sort.key === column.key ? (sort.desc ? ' ↓' : ' ↑') : ''}</button></th>)}</tr></thead><tbody>{sorted.map((row, i) => <tr key={row.province_code ? `${row.province_code}-${row.period || i}` : i}>{columns.map((column, ci) => <td key={column.key}>{ci === 0 && onRow ? <button className="table-link" onClick={() => onRow(row)}>{column.render ? column.render(row[column.key], row) : row[column.key]}<ArrowUpRight size={12}/></button> : column.render ? column.render(row[column.key], row) : row[column.key] ?? '—'}</td>)}</tr>)}</tbody></table>{!sorted.length && <Empty>Tidak ada hasil untuk pencarian ini.</Empty>}</div></>;
}

