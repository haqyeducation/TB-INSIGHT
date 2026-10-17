import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react';
import { monthLabel } from './data';

export default function MapTimeline({ data, filters, update }) {
  const [playing, setPlaying] = useState(false);
  const periods = data.meta.periods.filter((p) => p >= filters.start && p <= filters.end);
  const index = periods.indexOf(filters.period);
  const persistence = filters.layer === 'persistence';
  const spatialPeriods = data.meta.spatial_periods || [];

  useEffect(() => {
    if (!playing || persistence || periods.length < 2) return;
    const next = periods[(index + 1) % periods.length];
    const timer = setTimeout(() => update({ period: next }, { replace: true }), 1500);
    return () => clearTimeout(timer);
  }, [playing, persistence, filters.period, filters.start, filters.end, index, periods, update]);

  if (persistence) return <div className="static-period"><strong>{monthLabel(spatialPeriods[0])} – {monthLabel(spatialPeriods.at(-1))}</strong><span>Hasil persistence merangkum {spatialPeriods.length ? `${spatialPeriods.length} bulan lampiran` : 'periode lampiran yang belum tercatat'}. Tidak berubah dengan bulan fokus.</span></div>;
  return <div className="map-timeline" aria-label="Navigasi bulan peta">
    <div className="timeline-controls">
      <button className="icon-button" aria-label="Bulan sebelumnya" disabled={index <= 0} onClick={() => { setPlaying(false); update({ period: periods[index - 1] }); }}><ChevronLeft size={19}/></button>
      <button className="icon-button play-button" aria-label={playing ? 'Jeda animasi peta' : 'Putar animasi peta'} aria-pressed={playing} disabled={periods.length < 2} onClick={() => setPlaying(!playing)}>{playing ? <Pause size={18}/> : <Play size={18}/>}</button>
      <button className="icon-button" aria-label="Bulan berikutnya" disabled={index >= periods.length - 1} onClick={() => { setPlaying(false); update({ period: periods[index + 1] }); }}><ChevronRight size={19}/></button>
    </div>
    <label className="timeline-slider"><input aria-label="Geser bulan peta" type="range" min="0" max={Math.max(0, periods.length - 1)} value={Math.max(0, index)} disabled={periods.length < 2} onChange={(e) => { setPlaying(false); update({ period: periods[Number(e.target.value)] }, { replace: true }); }}/><div><small>{monthLabel(periods[0])}</small><small>{monthLabel(periods.at(-1))}</small></div></label>
    <span className="timeline-label"><strong>{monthLabel(filters.period)}</strong><small>{playing ? 'Berputar setiap 1,5 detik' : 'Bulan fokus'}</small></span>
  </div>;
}
