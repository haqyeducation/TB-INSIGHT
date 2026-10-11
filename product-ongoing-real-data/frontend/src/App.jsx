import { useEffect, useRef, useState } from 'react';
import { Activity, BookOpen, Database, LayoutDashboard, LineChart, Map, MapPin, RefreshCw } from 'lucide-react';
import { Empty, Note } from './components';
import { Overview, Trends, Maps, Province, Methods, Sources } from './pages';
import ProvinceMap from './ProvinceMap';
import Filters from './Filters';
import { useSnapshot } from './hooks';
import { downloadRows, monthLabel, LAYERS } from './data';

const NAV = [
  ['overview', 'Ringkasan', LayoutDashboard], ['trend', 'Tren', LineChart],
  ['map', 'Peta', Map], ['province', 'Provinsi', MapPin],
  ['methods', 'Metode', BookOpen], ['sources', 'Sumber', Database],
];
function readRoute() {
  const [path = '/overview', query = ''] = window.location.hash.slice(1).split('?');
  return { ...Object.fromEntries(new URLSearchParams(query)), page: NAV.some(([id]) => '/' + id === path) ? path.slice(1) : 'overview' };
}
function setRoute(route, { replace = false } = {}) {
  const { page, ...filters } = route;
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value != null && value !== '')).toString();
  const hash = `#/${page}${query ? '?' + query : ''}`;
  if (replace) {
    window.history.replaceState(null, '', hash);
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  } else window.location.hash = hash;
}
export default function App() {
  const snapshot = useSnapshot();
  const [route, setCurrentRoute] = useState(readRoute);
  const [filtersOpen, setFiltersOpen] = useState(() => window.innerWidth >= 768);
  const previousPage = useRef(route.page);
  useEffect(() => {
    const sync = () => {
      const next = readRoute();
      if (next.page !== previousPage.current) window.scrollTo({ top: 0 });
      previousPage.current = next.page;
      setCurrentRoute(next);
    };
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, []);
  const data = snapshot.data;
  const periods = data?.meta.periods || [];
  const start = periods.includes(route.start) ? route.start : periods[0];
  const end = periods.includes(route.end) && route.end >= start ? route.end : periods.at(-1);
  const filters = {
    province: data?.meta.provinces.some((p) => p.code === route.province) ? route.province : '', start, end,
    period: periods.includes(route.period) && route.period >= start && route.period <= end ? route.period : end,
    metric: route.metric === 'rate' ? 'rate' : 'count', layer: LAYERS[route.layer] ? route.layer : 'tb',
    overlays: [...new Set((route.overlays || '').split(',').filter((code) => code !== route.province && data?.meta.provinces.some((p) => p.code === code)))].slice(0, 3).join(','),
    from: route.from,
  };
  function update(changes, options) {
    const next = { ...filters, ...changes };
    if (next.start > next.end) {
      if (changes.start) next.end = next.start;
      else next.start = next.end;
    }
    if (next.period < next.start || next.period > next.end) next.period = next.end;
    setRoute({ ...next, page: route.page }, options);
  }
  function navigate(page, changes = {}) {
    setRoute({ ...filters, ...changes, from: page === 'province' ? (route.page === 'trend' ? 'trend' : 'map') : filters.from, page });
  }
  const exportData = (rows, filename, kind) => downloadRows(rows, 'tb-insight-' + filename, {
    dataset_version: data.meta.dataset_version, prepared_at: data.meta.prepared_at, filters,
    export_scope: { rows: rows.length, provinces: [...new Set(rows.map((r) => r.province_code).filter(Boolean))], periods: [...new Set(rows.map((r) => r.period).filter(Boolean))] },
    definition: 'Pasien mulai pengobatan TBC sensitif obat; bukan insidensi.',
    units: { count: 'pasien', rate: 'pasien per 100000 penduduk', pending: '%' },
    sources: data.meta.sources, input_files: data.meta.input_files,
    spatial_reconciliation: data.meta.spatial_reconciliation,
    note: 'Nilai tidak valid disembunyikan; outcome 2025 provisional. Lihat periode rujukan sosial. Tabel perbandingan dan peta mencakup seluruh provinsi, dengan wilayah aktif ditandai.',
  }, kind);
  const pageProps = { data, filters, update, navigate, exportData };
  const Page = { overview: Overview, trend: Trends, map: Maps, province: Province, methods: Methods, sources: Sources }[route.page];

  return <div className="app-shell">
    <a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); const main = document.getElementById('main-content'); main.focus(); main.scrollIntoView(); }}>Lewati ke konten</a>
    <header className="topbar">
      <a className="brand" href="#/overview" onClick={(e) => { e.preventDefault(); navigate('overview'); }}><span className="brand-mark"><Activity size={25}/></span><span>TB<span className="brand-light">INSIGHT</span><small>INDONESIA · DATA EXPLORER</small></span></a>
      <nav aria-label="Navigasi utama">{NAV.map(([id, label, Icon]) => <a key={id} href={`#/${id}${window.location.hash.includes('?') ? '?' + window.location.hash.split('?')[1] : ''}`} onClick={(e) => { e.preventDefault(); navigate(id); }} className={route.page === id ? 'active' : ''} aria-current={route.page === id ? 'page' : undefined}><Icon size={17}/>{label}</a>)}</nav>
      <span className="alpha-tag"><i/>Frontend alpha</span>
    </header>
    <div className="workspace-bar"><div><span className="live-dot"/><strong>Data sumber resmi</strong><span className="workspace-separator"/><span>{snapshot.mode === 'api' ? 'Snapshot melalui API' : snapshot.mode === 'snapshot' ? 'Snapshot lokal' : snapshot.mode === 'loading' ? 'Memuat snapshot…' : 'Data belum tersedia'}</span>{data && <span className="data-stamp">Disiapkan {new Date(data.meta.prepared_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}</span>}</div><button className="text-button" onClick={snapshot.retry} disabled={snapshot.mode === 'loading'}><RefreshCw size={15}/>Muat ulang</button></div>
    <main id="main-content" tabIndex="-1">
      {data && <>
        <Filters data={data} filters={filters} page={route.page} open={filtersOpen} setOpen={setFiltersOpen} update={update} reset={() => setRoute({ page: route.page })}/>
        {snapshot.mode === 'snapshot' && <Note>Menampilkan snapshot lokal yang disiapkan {new Date(data.meta.prepared_at).toLocaleString('id-ID')}. Endpoint dashboard belum aktif; data ini tersimpan dari sumber resmi, bukan pembaruan langsung.</Note>}
        <div key={route.page} className="page-content">
          <div className="page-breadcrumb"><span>Eksplorasi TB Indonesia</span><span aria-hidden="true">/</span><strong>{NAV.find(([id]) => id === route.page)?.[1]}</strong><span className="breadcrumb-period">{monthLabel(filters.period)}</span></div>
          {['methods', 'sources'].includes(route.page) && <p className="muted">Filter disimpan untuk eksplorasi. Dokumentasi dan sumber di halaman ini mencakup seluruh snapshot.</p>}
          <Page {...pageProps}/>
        </div>
      </>}
      {!data && snapshot.mode === 'loading' && <div className="loading-page" role="status"><span className="loader"/><h1>Menyiapkan ruang eksplorasi</h1><p>Memuat kohort, konteks wilayah, dan hasil spasial…</p><div className="skeleton-grid" aria-hidden="true"><i/><i/><i/></div></div>}
      {!data && snapshot.mode === 'error' && <><Empty retry={snapshot.retry}>{snapshot.error}</Empty><ProvinceMap data={null} filters={{}} neutral height={400}/></>}
    </main>
    <footer><div><strong>TBINSIGHT</strong><span>Eksplorasi pengobatan TB Indonesia</span></div><p>Data kohort pengobatan · bukan estimasi insidensi · hasil eksploratif</p><span>Frontend alpha</span></footer>
  </div>;
}
