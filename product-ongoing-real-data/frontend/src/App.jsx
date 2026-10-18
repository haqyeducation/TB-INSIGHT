import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Activity, AlertTriangle, ChevronRight, Database, Download, FileCheck2, FlaskConical, LayoutDashboard, Map as MapIcon, Search, ShieldCheck } from 'lucide-react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const API = import.meta.env.VITE_API_BASE_URL || '/api';
const nf = new Intl.NumberFormat('id-ID', { maximumFractionDigits: 2 });
const pages = [
  ['ringkasan', 'Ringkasan', LayoutDashboard], ['tren', 'Tren', Activity],
  ['peta', 'Peta', MapIcon], ['provinsi', 'Provinsi', Search],
  ['metode', 'Metode', FlaskConical], ['sumber', 'Sumber', Database],
];
const metricOptions = {
  rate: ['treatment_started_per_100k', 'Mulai pengobatan per 100.000'],
  count: ['jumlah_pasien', 'Jumlah mulai pengobatan'],
  precipitation: ['precipitation_mm_z', 'Anomali presipitasi'],
  poverty: ['poverty_pct', 'Kemiskinan BPS (%)'],
};

function useRoute() {
  const [route, setRoute] = useState(() => window.location.hash.slice(1) || 'ringkasan');
  useEffect(() => {
    const listener = () => setRoute(window.location.hash.slice(1) || 'ringkasan');
    window.addEventListener('hashchange', listener);
    return () => window.removeEventListener('hashchange', listener);
  }, []);
  return route;
}

function App() {
  const route = useRoute();
  const initial = new URLSearchParams(window.location.search);
  const [filters, setFilters] = useState({
    province: initial.get('province') || 'ALL', start: initial.get('start') || '2024-01',
    end: initial.get('end') || '2025-12', focus: initial.get('focus') || '2025-12',
    metric: initial.get('metric') || 'rate',
  });
  const [data, setData] = useState(null);
  const [lisa, setLisa] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/summary`), axios.get(`${API}/analysis/panel`),
      axios.get(`${API}/spatial/provinces`), axios.get(`${API}/provenance`),
      axios.get(`${API}/metadata`),
    ]).then(([summary, panel, boundary, provenance, metadata]) => setData({
      summary: summary.data, panel: panel.data, boundary: boundary.data,
      provenance: provenance.data, metadata: metadata.data,
    })).catch((err) => setError(err.response?.data?.detail || err.message));
  }, []);

  useEffect(() => {
    axios.get(`${API}/spatial/lisa`, { params: { period: filters.focus } })
      .then((response) => setLisa(response.data)).catch(() => setLisa([]));
    const query = new URLSearchParams(filters);
    window.history.replaceState(null, '', `${window.location.pathname}?${query}#${route}`);
  }, [filters, route]);

  const provinces = useMemo(() => data ? [...new Map(data.panel.map((r) => [r.province_code, r.province])).entries()] : [], [data]);
  const filtered = useMemo(() => data ? data.panel.filter((r) =>
    r.period >= filters.start && r.period <= filters.end &&
    (filters.province === 'ALL' || r.province_code === filters.province)) : [], [data, filters]);
  const focusRows = useMemo(() => data ? data.panel.filter((r) => r.period === filters.focus) : [], [data, filters.focus]);
  const series = useMemo(() => {
    const key = metricOptions[filters.metric][0];
    const grouped = new Map();
    filtered.forEach((row) => {
      const current = grouped.get(row.period) || { period: row.period, value: 0, n: 0 };
      current.value += Number(row[key] || 0); current.n += 1; grouped.set(row.period, current);
    });
    return [...grouped.values()].sort((a, b) => a.period.localeCompare(b.period)).map((row) => ({
      ...row, value: filters.metric === 'count' ? row.value : row.value / row.n,
    }));
  }, [filtered, filters.metric]);

  if (error) return <State icon={AlertTriangle} title="Data tidak dapat dimuat" text={error} />;
  if (!data) return <State icon={Database} title="Memuat data resmi" text="Menyiapkan panel dan geometri provinsi…" />;

  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value }));
  return <div className="shell">
    <aside className="sidebar">
      <a className="logo" href="#ringkasan"><span>TB</span><div>TB-INSIGHT<small>Indonesia</small></div></a>
      <nav>{pages.map(([id, label, Icon]) => <a key={id} href={`#${id}`} className={route === id ? 'active' : ''}><Icon size={18}/>{label}</a>)}</nav>
      <div className="verified"><ShieldCheck size={19}/><div><strong>Real data only</strong><small>Kemenkes · BPS · NASA · BIG · BNPB</small></div></div>
    </aside>
    <div className="workspace">
      <header><div><span className="kicker">TB surveillance workspace</span><h1>{pages.find((p) => p[0] === route)?.[1] || 'Ringkasan'}</h1></div><a className="download" href={`${API}/download/panel.csv`}><Download size={16}/> Unduh panel</a></header>
      <FilterBar filters={filters} provinces={provinces} update={update}/>
      <main>
        {route === 'ringkasan' && <Summary data={data} filtered={filtered} />}
        {route === 'tren' && <Trend series={series} filters={filters} />}
        {route === 'peta' && <SpatialMap boundary={data.boundary} rows={focusRows} lisa={lisa} filters={filters} />}
        {route === 'provinsi' && <ProvinceProfile rows={filtered} provinces={provinces} filters={filters} update={update} />}
        {route === 'metode' && <Methods />}
        {route === 'sumber' && <Sources provenance={data.provenance} metadata={data.metadata} />}
      </main>
    </div>
  </div>;
}

function FilterBar({ filters, provinces, update }) {
  return <section className="filters">
    <label>Wilayah<select value={filters.province} onChange={(e) => update('province', e.target.value)}><option value="ALL">Seluruh Indonesia</option>{provinces.map(([code, name]) => <option value={code} key={code}>{name}</option>)}</select></label>
    <label>Dari<input type="month" value={filters.start} min="2024-01" max="2025-12" onChange={(e) => update('start', e.target.value)}/></label>
    <label>Sampai<input type="month" value={filters.end} min="2024-01" max="2025-12" onChange={(e) => update('end', e.target.value)}/></label>
    <label>Bulan peta<input type="month" value={filters.focus} min="2024-01" max="2025-12" onChange={(e) => update('focus', e.target.value)}/></label>
    <label>Indikator<select value={filters.metric} onChange={(e) => update('metric', e.target.value)}>{Object.entries(metricOptions).map(([key, [, label]]) => <option value={key} key={key}>{label}</option>)}</select></label>
  </section>;
}

function Summary({ data, filtered }) {
  const total = filtered.reduce((sum, row) => sum + Number(row.jumlah_pasien), 0);
  const pending = filtered.reduce((sum, row) => sum + Number(row.belum_ada_hasil), 0);
  const mature = filtered.filter((row) => row.cohort_maturity_flag === 'mature_le_5pct_pending').length;
  return <><section className="hero"><div><span className="pill"><FileCheck2 size={15}/> Panel tervalidasi</span><h2>Melihat pola TB, iklim, dan kerentanan sosial tanpa menyamarkan keterbatasan data.</h2><p>Unit analisis adalah provinsi-bulan. Outcome merupakan kohort pasien yang memulai pengobatan TBC sensitif obat, bukan estimasi insidensi.</p></div><div className="notice"><AlertTriangle/><div><strong>2025 masih provisional</strong><span>Outcome pasien dapat berubah saat kohort menjadi lebih matang. Gunakan jumlah mulai pengobatan sebagai outcome utama.</span></div></div></section>
  <section className="cards"><Card label="Mulai pengobatan" value={nf.format(total)} note={`${filtered.length} observasi provinsi-bulan`}/><Card label="Outcome tertunda" value={nf.format(pending)} note="Belum ada hasil"/><Card label="Kohort matang" value={`${mature}/${filtered.length}`} note="Pending ≤ 5%"/><Card label="Cakupan" value={`${data.summary.province_count} provinsi`} note="Januari 2024–Desember 2025"/></section>
  <section className="panel next"><div><span className="kicker">Mulai eksplorasi</span><h3>Alur analisis yang disarankan</h3></div><div className="steps"><a href="#tren">1. Periksa tren temporal<ChevronRight/></a><a href="#peta">2. Bandingkan pola spasial<ChevronRight/></a><a href="#provinsi">3. Baca profil provinsi<ChevronRight/></a><a href="#metode">4. Verifikasi metode<ChevronRight/></a></div></section></>;
}

function Trend({ series, filters }) {
  return <section className="panel"><div className="panel-head"><div><span className="kicker">Seri waktu</span><h2>{metricOptions[filters.metric][1]}</h2><p>Rentang {filters.start}—{filters.end}. Garis agregat berupa jumlah untuk count dan rerata provinsi untuk indikator lain.</p></div></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={series}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="period"/><YAxis/><Tooltip formatter={(v) => nf.format(v)}/><Legend/><Line dataKey="value" name={metricOptions[filters.metric][1]} stroke="#0f766e" strokeWidth={3} dot={{ r: 3 }} isAnimationActive={false}/></LineChart></ResponsiveContainer></div><p className="caption">Perubahan temporal bersifat deskriptif; dua tahun data belum cukup untuk menyimpulkan siklus iklim jangka panjang.</p></section>;
}

function SpatialMap({ boundary, rows, lisa, filters }) {
  const key = metricOptions[filters.metric][0];
  const values = rows.map((r) => Number(r[key])).filter(Number.isFinite);
  const min = Math.min(...values), max = Math.max(...values);
  const lookup = new globalThis.Map(rows.map((r) => [r.province_code, r]));
  const lisaLookup = new globalThis.Map(lisa.map((r) => [r.province_code, r]));
  const color = (value) => { const t = max === min ? .5 : (value - min) / (max - min); return t > .8 ? '#7f1d1d' : t > .6 ? '#dc2626' : t > .4 ? '#f97316' : t > .2 ? '#facc15' : '#d9f99d'; };
  return <div className="map-layout"><section className="panel map-panel"><div className="panel-head"><div><span className="kicker">BIG · {filters.focus}</span><h2>{metricOptions[filters.metric][1]}</h2><p>Hover wilayah untuk nilai dan klasifikasi LISA. Bridge antarpulau hanya dipakai dalam analisis bobot.</p></div></div><MapContainer center={[-2.4, 118]} zoom={5} scrollWheelZoom className="map"><TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><GeoJSON key={`${filters.focus}-${filters.metric}`} data={boundary} style={(feature) => { const row = lookup.get(String(feature.properties.province_code).padStart(2, '0')); return { color: '#fff', weight: .7, fillOpacity: .82, fillColor: row ? color(Number(row[key])) : '#cbd5e1' }; }} onEachFeature={(feature, layer) => { const code = String(feature.properties.province_code).padStart(2, '0'); const row = lookup.get(code); const spot = lisaLookup.get(code); layer.bindTooltip(`<strong>${feature.properties.province}</strong><br/>${row ? nf.format(row[key]) : 'Tidak tersedia'}<br/>LISA FDR: ${spot?.cluster_fdr_0_05 || '—'}`); }}/></MapContainer></section><section className="panel legend"><h3>Legenda</h3><p>Warna relatif terhadap rentang bulan terpilih.</p><div className="gradient"/><div className="range"><span>{nf.format(min)}</span><span>{nf.format(max)}</span></div><hr/><h3>LISA</h3><p>{lisa.filter((r) => r.cluster_fdr_0_05 !== 'not_significant').length} provinsi signifikan setelah FDR pada bulan ini.</p><small>999 permutasi; queen contiguity + bridge terpendek yang terdokumentasi.</small></section></div>;
}

function ProvinceProfile({ rows, provinces, filters, update }) {
  const code = filters.province === 'ALL' ? provinces[0]?.[0] : filters.province;
  const selected = rows.filter((r) => r.province_code === code);
  const latest = selected[selected.length - 1];
  return <><section className="panel profile-head"><div><span className="kicker">Profil wilayah</span><h2>{latest?.province || 'Pilih provinsi'}</h2><p>Pilih wilayah pada filter global untuk melihat seri dan konteks sosialnya.</p></div>{filters.province === 'ALL' && <button onClick={() => update('province', code)}>Gunakan {latest?.province}</button>}</section>{latest && <section className="cards"><Card label="Mulai pengobatan terakhir" value={nf.format(latest.jumlah_pasien)} note={latest.period}/><Card label="Per 100.000" value={nf.format(latest.treatment_started_per_100k)} note="Penduduk BPS sebagai denominator"/><Card label="Kemiskinan" value={`${nf.format(latest.poverty_pct)}%`} note={latest.poverty_reference_period}/><Card label="Sanitasi" value={`${nf.format(latest.sanitation_access_pct)}%`} note={latest.sanitation_reference_period}/></section>}<section className="panel table-wrap"><table><thead><tr><th>Periode</th><th>Mulai pengobatan</th><th>Per 100k</th><th>Pending</th><th>Suhu z</th><th>Hujan z</th><th>Bencana</th></tr></thead><tbody>{selected.map((r) => <tr key={r.period}><td>{r.period}</td><td>{nf.format(r.jumlah_pasien)}</td><td>{nf.format(r.treatment_started_per_100k)}</td><td>{nf.format(r.pending_share * 100)}%</td><td>{nf.format(r.temperature_c_z)}</td><td>{nf.format(r.precipitation_mm_z)}</td><td>{nf.format(r.event_record_count)}</td></tr>)}</tbody></table></section></>;
}

function Methods() { return <section className="method-grid"><article className="panel"><span className="kicker">Unit analisis</span><h2>38 provinsi × 24 bulan</h2><p>Panel lengkap Januari 2024–Desember 2025. Populasi tahunan dipakai sebagai offset; kemiskinan dan sanitasi mempertahankan periode surveinya.</p></article><article className="panel"><span className="kicker">Model primer</span><h2>PPML fixed effects</h2><p>Outcome jumlah mulai pengobatan, offset log-populasi, fixed effects provinsi dan periode, serta standard error terklaster provinsi.</p></article><article className="panel"><span className="kicker">Spasial</span><h2>Queen + bridge transparan</h2><p>Kontiguitas darat dibangun dari BIG. Komponen kepulauan disambung melalui jarak polygon terpendek dan setiap bridge ditandai eksplisit.</p></article><article className="panel"><span className="kicker">Inferensi</span><h2>Eksploratif, bukan kausal</h2><p>Lag 0–3 dan sembilan interaksi sosial dilaporkan tanpa memilih hasil berdasarkan p-value. LISA menggunakan 999 permutasi dan FDR bulanan.</p></article></section>; }

function Sources({ provenance, metadata }) { return <><section className="source-grid">{provenance.map((s) => <article className="panel" key={s.dataset_id}><Database/><span className="kicker">{s.publisher}</span><h3>{s.dataset_id}</h3><p>{s.coverage}</p><small>{s.limitation}</small><a href={s.source_url.split(' ; ')[0]} target="_blank" rel="noreferrer">Buka sumber resmi <ChevronRight size={15}/></a></article>)}</section><section className="panel"><h3>Batas penggunaan</h3><ul className="limitations">{metadata.limitations.map((item) => <li key={item}>{item}</li>)}</ul></section></>; }
function Card({ label, value, note }) { return <article><span>{label}</span><strong>{value}</strong><small>{note}</small></article>; }
function State({ icon: Icon, title, text }) { return <main className="state"><Icon/><h1>{title}</h1><p>{text}</p></main>; }

export default App;
