import { useReducedMotion } from './hooks';
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { geoJSON } from 'leaflet';
import { GeoJSON, MapContainer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { LocateFixed, MapPin, MousePointer2 } from 'lucide-react';
import { format, titleCase, monthLabel, LAYERS, mapRecords, scaleFor } from './data';
import { DataStates, Empty, SourceNote } from './components';
import { COLORS } from './theme';

let geometryRequest;
function loadGeometry() {
  if (!geometryRequest) geometryRequest = fetch('/maps/provinces.geojson').then((r) => {
    if (!r.ok) throw new Error('Boundary unavailable');
    return r.json();
  }).catch((error) => { geometryRequest = null; throw error; });
  return geometryRequest;
}
const COUNTRY_BOUNDS = [[-11.5, 94], [6.5, 142]];

function Viewport({ reset, focus, province, geometry, reduced }) {
  const map = useMap();
  useEffect(() => {
    const bounds = focus && province
      ? geoJSON({ type: 'FeatureCollection', features: geometry.features.filter((f) => f.properties.province_code === province) }).getBounds()
      : COUNTRY_BOUNDS;
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 7, animate: !reduced, duration: 0.5 });
  }, [map, reset, focus, province, geometry, reduced]);
  useEffect(() => {
    let frame;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        map.invalidateSize();
        map.fitBounds(COUNTRY_BOUNDS, { padding: [24, 24], animate: false });
      });
    });
    observer.observe(map.getContainer());
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [map]);
  return null;
}

function tooltipContent(feature, record, { layerId, unit, filters, data, neutral }) {
  const container = document.createElement('div');
  const append = (tag, text) => { const el = document.createElement(tag); el.textContent = text; container.append(el); };
  append('strong', titleCase(feature.properties.province_name));
  append('div', neutral ? 'Batas provinsi' : record?.state?.kind === 'missing' || record?.state?.kind === 'invalid'
    ? record.state.label : `${typeof record?.value === 'number' ? format(record.value, 2) : record?.value ?? 'Belum tersedia'} ${typeof record?.value === 'number' ? unit : ''}`);
  const reference = layerId === 'poverty' ? record?.detail?.poverty_reference_period : layerId === 'sanitation' ? record?.detail?.sanitation_reference_period : record?.detail?.population_reference_date;
  append('small', layerId === 'persistence' ? `${monthLabel(data?.meta.periods[0])}–${monthLabel(data?.meta.periods.at(-1))} · lampiran Dame`
    : LAYERS[layerId]?.social ? `Bulan panel ${monthLabel(filters.period)} · rujukan ${reference || 'belum tersedia'}` : monthLabel(filters.period));
  if (!neutral && record?.detail) {
    append('div', layerId === 'tb' ? `${format(record.detail.treatment_started)} pasien · rate ${format(record.detail.rate_per_100k, 2)} /100.000 · pending ${format(record.detail.pending_share_pct, 1)}%`
      : layerId === 'lisa' ? `p-FDR ${format(record.detail.p_fdr, 4)} · ${record.detail.quadrant}`
        : layerId === 'persistence' ? `${format(record.detail.n_HH)} bulan HH · ${format(record.detail.n_LL)} bulan LL signifikan` : LAYERS[layerId].source);
    if (layerId === 'tb') append('small', record.detail.revision_status === 'provisional' ? 'Kohort provisional' : 'Status revisi belum diketahui');
  }
  append('small', 'Klik untuk membuka profil provinsi');
  return container;
}

function Regions({ geometry, index, scale, filters, layerId, unit, data, neutral, onSelect, onHover, patternId }) {
  const group = useRef(null);
  useEffect(() => {
    if (!group.current) return;
    const layerGroup = group.current;
    const mainRegion = new Map();
    layerGroup.eachLayer((region) => {
      const code = region.feature.properties.province_code;
      const bounds = region.getBounds();
      const size = (bounds.getEast() - bounds.getWest()) * (bounds.getNorth() - bounds.getSouth());
      if (!mainRegion.has(code) || size > mainRegion.get(code).size) mainRegion.set(code, { region, size });
    });
    const styleFor = (feature) => {
      const code = feature.properties.province_code;
      const record = index[code];
      const state = record?.state?.kind;
      return {
        color: code === filters.province ? COLORS.ink : '#FFFFFF',
        weight: code === filters.province ? 2.8 : 0.6,
        fillColor: neutral ? COLORS.ice : state === 'invalid' ? `url(#${patternId}-invalid)`
          : state === 'missing' || record?.value == null ? `url(#${patternId}-missing)` : scale.color(record.value),
        fillOpacity: 1,
        dashArray: !neutral && (state === 'missing' || state === 'invalid') ? '3 3' : null,
      };
    };
    const highlight = (code) => layerGroup.eachLayer((region) => {
      if (region.feature.properties.province_code === code) region.setStyle({ color: COLORS.ink, weight: 2.6 });
    });
    const clear = () => { layerGroup.eachLayer((region) => region.setStyle(styleFor(region.feature))); onHover(null); };
    layerGroup.eachLayer((region) => {
      const code = region.feature.properties.province_code;
      const record = index[code];
      region.setStyle(styleFor(region.feature));
      region.unbindTooltip();
      region.bindTooltip(tooltipContent(region.feature, record, { layerId, unit, filters, data, neutral }), { sticky: true, className: 'province-tooltip', opacity: 1 });
      region.off('click mouseover mouseout');
      region.on({ click: () => onSelect?.(code), mouseover: () => { highlight(code); onHover(code); }, mouseout: clear });
      const element = region.getElement();
      if (element) {
        element.setAttribute('role', 'button');
        element.setAttribute('aria-label', `Buka profil ${titleCase(region.feature.properties.province_name)}`);
        element.setAttribute('tabindex', mainRegion.get(code).region === region ? '0' : '-1');
        element.onkeydown = (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect?.(code); } };
        element.onfocus = () => { highlight(code); onHover(code); region.openTooltip(); };
        element.onblur = () => { clear(); region.closeTooltip(); };
      }
    });
    return () => layerGroup.eachLayer((region) => {
      region.off('click mouseover mouseout');
      const element = region.getElement();
      if (element) element.onkeydown = element.onfocus = element.onblur = null;
    });
  }, [geometry, index, scale, filters, layerId, unit, data, neutral, onSelect, onHover, patternId]);
  return <GeoJSON ref={group} data={geometry}/>;
}

export default function ProvinceMap({ data, filters, layerId = 'tb', onSelect, height = 430, neutral = false }) {
  const [geometry, setGeometry] = useState(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [reset, setReset] = useState(0);
  const [focus, setFocus] = useState(0);
  const [hover, setHover] = useState(null);
  const reduced = useReducedMotion();
  const patternId = useId().replaceAll(':', '');
  useEffect(() => {
    let active = true;
    loadGeometry().then((json) => { if (active) { setGeometry(json); setError(false); } }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [attempt]);
  const records = useMemo(() => data ? mapRecords(data, filters, layerId) : [], [data, filters, layerId]);
  const index = useMemo(() => Object.fromEntries(records.map((r) => [r.code, r])), [records]);
  const scale = useMemo(() => data ? scaleFor(data, layerId, filters.metric) : null, [data, layerId, filters.metric]);
  const unit = layerId === 'tb' ? (filters.metric === 'rate' ? 'pasien / 100.000' : 'pasien') : LAYERS[layerId].unit;
  const record = index[hover];
  const missing = records.filter((r) => r.state.kind === 'missing').length;
  const invalid = records.filter((r) => r.state.kind === 'invalid').length;
  if (error) return <Empty retry={() => { setError(false); setAttempt((v) => v + 1); }}>Masih memerlukan data batas provinsi GeoJSON yang dapat dibaca.</Empty>;
  if (!geometry) return <div className="map-loading" style={{ height }} role="status"><span className="loader"/>Memuat batas wilayah…</div>;
  return <div className="map-block">
    <svg className="map-patterns" aria-hidden="true"><defs>
      <pattern id={`${patternId}-missing`} width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#F1F5F7"/><path d="M0 8 L8 0" stroke="#B7C7D0" strokeWidth="1.4"/></pattern>
      <pattern id={`${patternId}-invalid`} width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#EDF0FB"/><path d="M0 0 L8 8 M8 0 L0 8" stroke="#8891BF" strokeWidth="1.2"/></pattern>
    </defs></svg>
    <div className="map-canvas" style={{ height }}>
      <MapContainer center={[-2.5, 118]} zoom={3} minZoom={2} maxZoom={9} zoomSnap={0.25} zoomDelta={0.5} scrollWheelZoom={false} attributionControl={false} zoomAnimation={!reduced} fadeAnimation={!reduced} style={{ height: '100%', width: '100%' }}>
        <Viewport reset={reset} focus={focus} province={filters.province} geometry={geometry} reduced={reduced}/>
        <Regions geometry={geometry} index={index} scale={scale} filters={filters} layerId={layerId} unit={unit} data={data} neutral={neutral} onSelect={onSelect} onHover={setHover} patternId={patternId}/>
      </MapContainer>
      <div className="map-controls"><button onClick={() => { setFocus(0); setReset((n) => n + 1); }} title="Tampilkan seluruh Indonesia"><LocateFixed size={16}/>Indonesia</button>{filters.province && <button onClick={() => setFocus((n) => n + 1)}><MapPin size={16}/>Fokus wilayah</button>}</div>
      <span className="map-attribution">Batas BIG · generalisasi</span>
    </div>
    <div className={`map-hover-card ${hover ? 'has-region' : ''}`} aria-live="polite">
      {hover ? <><MapPin size={18}/><strong>{titleCase(record?.name || geometry.features.find((f) => f.properties.province_code === hover)?.properties.province_name)}</strong><span>{neutral ? 'Batas wilayah' : record?.state?.kind === 'missing' || record?.state?.kind === 'invalid' ? record.state.label : `${typeof record?.value === 'number' ? format(record.value, 2) : record?.value ?? 'Belum tersedia'} ${typeof record?.value === 'number' ? unit : ''}`}</span></> : <><MousePointer2 size={18}/><span>Arahkan kursor untuk nilai. Klik wilayah untuk membuka profil.</span></>}
    </div>
    {scale && !neutral && <div className="map-legend" aria-label="Legenda peta">{scale.categorical ? scale.labels.map((label, i) => <span key={label}><i style={{ background: scale.colors[i] }}/>{label}</span>) : <><strong>{unit}</strong>{scale.colors.map((color, i) => <span key={i}><i style={{ background: color }}/>{format(scale.boundaries[i], 1)}–{format(scale.boundaries[i + 1], 1)}</span>)}</>}
      {missing > 0 && <span><i className="state-missing"/>Belum tersedia ({missing})</span>}{invalid > 0 && <span><i className="state-invalid"/>Belum valid ({invalid})</span>}
    </div>}
    <p className="map-caption">{neutral ? 'Peta batas provinsi. Pilih wilayah untuk menjelajahi data.' : scale?.categorical ? 'Kategori mengikuti lampiran Dame. Not significant tidak berarti tidak ada pasien TB.' : 'Lima interval sama lebar, tetap sepanjang dataset. Warna menunjukkan nilai indikator; bukan kategori risiko.'}</p>
    {!neutral && <><DataStates/><SourceNote indicator={layerId}/></>}
  </div>;
}
