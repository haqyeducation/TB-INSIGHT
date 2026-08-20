import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  AlertCircle, Database, ExternalLink, FileCheck2,
  LineChart as LineChartIcon, MapPinned, ShieldCheck,
} from 'lucide-react';
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

const API = import.meta.env.VITE_API_BASE_URL || '/api';
const nf = new Intl.NumberFormat('id-ID');
const pct = (value) => value == null ? '—' : `${nf.format(value)}%`;
const indicatorLabels = {
  suspected: 'Terduga', tested: 'Testing', notified: 'Notifikasi kasus', treated: 'Memulai pengobatan',
};
const colors = { suspected: '#0f766e', tested: '#2563eb', notified: '#dc2626', treated: '#7c3aed' };

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [trendYear, setTrendYear] = useState(2024);
  const [bpsYear, setBpsYear] = useState(2024);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/summary`), axios.get(`${API}/tb/national-monthly`),
      axios.get(`${API}/analysis/province-2024`), axios.get(`${API}/bps/province-annual`),
      axios.get(`${API}/metadata`),
    ])
      .then(([summary, monthly, province, bps, metadata]) => setData({
        summary: summary.data, monthly: monthly.data, province: province.data,
        bps: bps.data, metadata: metadata.data,
      }))
      .catch((requestError) => setError(requestError.response?.data?.detail || requestError.message));
  }, []);

  const trend = useMemo(() => {
    if (!data) return [];
    const rows = data.monthly.filter((row) => Number(row.year) === trendYear);
    return [...new Set(rows.map((row) => row.period))].sort().map((period) => {
      const point = { period: period.slice(5) };
      rows.filter((row) => row.period === period).forEach((row) => { point[row.indicator] = row.value; });
      return point;
    });
  }, [data, trendYear]);

  const provinceRows = useMemo(() => data
    ? [...data.province].sort((a, b) => b.tb_cases_total - a.tb_cases_total)
    : [], [data]);
  const bpsRows = useMemo(() => data
    ? data.bps.filter((row) => Number(row.year) === bpsYear).sort((a, b) => b.population - a.population)
    : [], [data, bpsYear]);

  if (error) return <main className="center-state"><AlertCircle /><h1>Data belum dapat dimuat</h1><p>{error}</p></main>;
  if (!data) return <main className="center-state"><Database className="pulse" /><h1>Memuat data resmi…</h1></main>;

  const topTen = provinceRows.slice(0, 10).map((row) => ({ province: row.province, cases: row.tb_cases_total }));

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#overview"><span className="brand-mark">TB</span><span>TB-INSIGHT<small>Indonesia · data resmi</small></span></a>
        <nav><a href="#trend">Tren nasional</a><a href="#province">Provinsi</a><a href="#bps">BPS</a><a href="#sources">Sumber</a></nav>
      </header>

      <main>
        <section className="hero" id="overview">
          <div>
            <span className="eyebrow"><ShieldCheck size={16}/> Dataset terverifikasi</span>
            <h1>Pemantauan TBC Indonesia berbasis data pemerintah</h1>
            <p>Seri nasional bulanan SITB, indikator provinsi Kemenkes, dan kovariat resmi BPS. Setiap periode dan keterbatasan dipertahankan tanpa imputasi geografis.</p>
          </div>
          <div className="hero-status">
            <FileCheck2 size={22}/><div><strong>Provinsi-bulanan resmi sudah tersedia</strong><span>{data.summary.province_month_status}. Interpretasikan sebagai kohort mulai pengobatan, bukan insidensi.</span></div>
          </div>
        </section>

        <section className="stats-grid">
          <article><FileCheck2/><span>Kasus TBC 2024</span><strong>{nf.format(data.summary.tb_cases_2024)}</strong><small>Kemenkes · 38 provinsi</small></article>
          <article><MapPinned/><span>Cakupan wilayah</span><strong>{data.summary.province_count} provinsi</strong><small>Bulanan 2024-2025</small></article>
          <article><LineChartIcon/><span>Seri nasional</span><strong>{data.summary.national_month_indicators} indikator</strong><small>{data.summary.national_month_period_min}—{data.summary.national_month_period_max}</small></article>
          <article><Database/><span>Kovariat BPS</span><strong>2023—2026</strong><small>Periode asli dipertahankan</small></article>
        </section>

        <section className="panel" id="trend">
          <div className="section-heading"><div><span className="eyebrow">SITB · nasional bulanan</span><h2>Alur penemuan dan pengobatan TBC</h2><p>Nilai bulanan hasil ekspor crosstab Dashboard TB Kemenkes.</p></div><label>Tahun<select value={trendYear} onChange={(event) => setTrendYear(Number(event.target.value))}>{[2023, 2024, 2025, 2026].map((year) => <option key={year}>{year}</option>)}</select></label></div>
          <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><LineChart data={trend}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="period"/><YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`}/><Tooltip formatter={(value, name) => [nf.format(value), indicatorLabels[name]]}/><Legend formatter={(name) => indicatorLabels[name]}/>{Object.keys(indicatorLabels).map((key) => <Line key={key} type="monotone" dataKey={key} stroke={colors[key]} strokeWidth={3} dot={{ r: 3 }} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div>
          {trendYear === 2026 && <p className="footnote">Seri 2026 pada sumber publik tersedia sampai Juni 2026; jangan membandingkan total tahun berjalan langsung dengan total tahun penuh.</p>}
        </section>

        <section className="two-column" id="province">
          <article className="panel">
            <div className="section-heading compact"><div><span className="eyebrow">Kemenkes · 2024</span><h2>10 provinsi dengan kasus terbanyak</h2></div></div>
            <div className="chart-wrap tall"><ResponsiveContainer width="100%" height="100%"><BarChart data={topTen} layout="vertical" margin={{ left: 42 }}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" tickFormatter={(value) => `${Math.round(value / 1000)}k`}/><YAxis type="category" dataKey="province" width={112} tick={{ fontSize: 11 }}/><Tooltip formatter={(value) => nf.format(value)}/><Bar dataKey="cases" fill="#0f766e" radius={[0, 6, 6, 0]} isAnimationActive={false}/></BarChart></ResponsiveContainer></div>
          </article>
          <article className="panel table-panel">
            <div className="section-heading compact"><div><span className="eyebrow">Panel analisis · 2024</span><h2>TB dan konteks BPS</h2></div></div>
            <div className="table-scroll"><table><thead><tr><th>Provinsi</th><th>Kasus</th><th>CNR/100k</th><th>TC</th><th>Penduduk</th><th>Kepadatan</th><th>Sanitasi</th></tr></thead><tbody>{provinceRows.map((row) => <tr key={row.province_code}><td>{row.province}</td><td>{nf.format(row.tb_cases_total)}</td><td>{nf.format(row.case_notification_rate_per_100k)}</td><td>{pct(row.treatment_coverage_pct)}</td><td>{nf.format(row.population)}</td><td>{nf.format(row.population_density_per_km2)}</td><td>{pct(row.sanitation_access_pct)}</td></tr>)}</tbody></table></div>
          </article>
        </section>

        <section className="panel table-panel" id="bps">
          <div className="section-heading"><div><span className="eyebrow">BPS · 38 provinsi</span><h2>Kovariat sosial-demografi</h2><p>Populasi dan kepadatan adalah proyeksi pertengahan tahun. Kemiskinan dan sanitasi mengikuti periode survei yang tercantum.</p></div><label>Tahun<select value={bpsYear} onChange={(event) => setBpsYear(Number(event.target.value))}>{[2023, 2024, 2025, 2026].map((year) => <option key={year}>{year}</option>)}</select></label></div>
          <div className="table-scroll bps-table"><table><thead><tr><th>Provinsi</th><th>Penduduk</th><th>Jiwa/km²</th><th>Akses sanitasi</th><th>Kemiskinan</th><th>Periode rujukan</th></tr></thead><tbody>{bpsRows.map((row) => <tr key={`${row.province_code}-${row.year}`}><td>{row.province}</td><td>{nf.format(row.population)}</td><td>{nf.format(row.population_density_per_km2)}</td><td>{pct(row.sanitation_access_pct)}</td><td>{pct(row.poverty_pct)}</td><td>{row.poverty_reference_period || row.sanitation_reference_period || row.population_reference_date}</td></tr>)}</tbody></table></div>
          <p className="footnote">Tanda “—” berarti indikator tersebut tidak tersedia untuk periode itu; nilai tidak diisi dengan interpolasi.</p>
        </section>

        <section className="panel" id="sources">
          <div className="section-heading compact"><div><span className="eyebrow">Provenance</span><h2>Sumber dan batas penggunaan</h2></div></div>
          <div className="source-grid">{data.metadata.sources.map((source) => <a key={source.dataset} href={source.url} target="_blank" rel="noreferrer"><Database/><div><strong>{source.dataset}</strong><span>{source.publisher}</span><small>{source.coverage}</small></div><ExternalLink size={17}/></a>)}</div>
          <div className="limitations"><h3><AlertCircle size={18}/> Batas interpretasi</h3><ul>{data.metadata.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
        </section>
      </main>
      <footer>TB-INSIGHT · pipeline reproducible untuk data resmi Kemenkes dan BPS</footer>
    </div>
  );
}

export default App;
