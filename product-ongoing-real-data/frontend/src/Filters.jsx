import { ChevronDown, RotateCcw, SlidersHorizontal, X } from 'lucide-react';
import { monthLabel, titleCase } from './data';

export default function Filters({ data, filters, page, open, setOpen, update, reset }) {
  const periods = data.meta.periods;
  const scope = filters.province
    ? titleCase(data.meta.provinces.find((p) => p.code === filters.province)?.name)
    : 'Seluruh Indonesia';
  const persistence = page === 'map' && filters.layer === 'persistence';
  const metricDisabled = page === 'map' && filters.layer !== 'tb';
  const years = [...new Set(periods.map((p) => p.slice(0, 4)))];

  function selectYear(year) {
    const selected = year ? periods.filter((p) => p.startsWith(year)) : periods;
    update({ start: selected[0], end: selected.at(-1), period: selected.at(-1) });
  }

  return <section className="filter-panel" aria-label="Filter dashboard">
    <div className="filter-label">
      <span><SlidersHorizontal size={18}/><strong>Atur eksplorasi</strong><small>Filter dibawa ke setiap halaman</small></span>
      <div className="filter-actions">
        <button className="text-button" onClick={reset} aria-label="Reset filter"><RotateCcw size={15}/>Reset</button>
        <button className="text-button" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? 'Sembunyikan' : 'Tampilkan'}<ChevronDown size={16} className={open ? 'rotate' : ''}/></button>
      </div>
    </div>
    {open && <div className="filter-body">
      <div className="filter-grid">
        <label><span className="filter-step">1</span> Wilayah
          <select aria-label="Wilayah" value={filters.province} onChange={(e) => update({ province: e.target.value })}>
            <option value="">Seluruh Indonesia</option>
            {data.meta.provinces.map((p) => <option key={p.code} value={p.code}>{titleCase(p.name)}</option>)}
          </select>
        </label>
        <fieldset className="range-filter"><legend><span className="filter-step">2</span> Rentang tren</legend>
          <div><label>Dari<select aria-label="Dari bulan" value={filters.start} onChange={(e) => update({ start: e.target.value })}>{periods.map((p) => <option key={p} value={p}>{monthLabel(p)}</option>)}</select></label>
            <label>Sampai<select aria-label="Sampai bulan" value={filters.end} onChange={(e) => update({ end: e.target.value })}>{periods.map((p) => <option key={p} value={p}>{monthLabel(p)}</option>)}</select></label></div>
        </fieldset>
        <label><span className="filter-step">3</span> Bulan fokus
          <select aria-label="Bulan fokus" value={filters.period} disabled={persistence} onChange={(e) => update({ period: e.target.value })}>{periods.filter((p) => p >= filters.start && p <= filters.end).map((p) => <option key={p} value={p}>{monthLabel(p)}</option>)}</select>
          {persistence && <small>Persistence memakai seluruh periode lampiran.</small>}
        </label>
        <div className="metric-filter"><span><span className="filter-step">4</span> Metrik TB</span>
          <div role="group" aria-label="Metrik TB">
            <button disabled={metricDisabled} aria-pressed={filters.metric === 'count'} className={filters.metric === 'count' ? 'active' : ''} onClick={() => update({ metric: 'count' })}>Jumlah</button>
            <button disabled={metricDisabled} aria-pressed={filters.metric === 'rate'} className={filters.metric === 'rate' ? 'active' : ''} onClick={() => update({ metric: 'rate' })}>Per 100.000</button>
          </div>
          {metricDisabled && <small>Satuan mengikuti layer peta.</small>}
        </div>
      </div>
      <div className="period-presets"><span>Rentang cepat</span><button onClick={() => selectYear('')} className={filters.start === periods[0] && filters.end === periods.at(-1) ? 'active' : ''}>Seluruh periode</button>{years.map((year) => <button key={year} onClick={() => selectYear(year)} className={filters.start?.startsWith(year) && filters.end?.startsWith(year) ? 'active' : ''}>{year}</button>)}</div>
    </div>}
    <div className="filter-context" aria-label="Konteks analisis">
      {filters.province ? <button className="context-chip" onClick={() => update({ province: '' })} aria-label="Hapus filter provinsi">{scope}<X size={13}/></button> : <span className="context-chip">{scope}</span>}
      <span>{monthLabel(filters.start)} – {monthLabel(filters.end)}</span>
      <span>{persistence ? `Persistence · ${data.meta.spatial_periods?.length ? `${data.meta.spatial_periods.length} bulan lampiran` : 'periode belum tercatat'}` : `Fokus ${monthLabel(filters.period)}`}</span>
      {filters.period?.startsWith('2025') && !persistence && <span className="provisional-pill">Kohort provisional</span>}
    </div>
  </section>;
}
