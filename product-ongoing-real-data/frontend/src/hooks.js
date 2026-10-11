import { useEffect, useState } from 'react';

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const media = window.matchMedia('(prefers-reduced-motion: reduce)'); const sync = () => setReduced(media.matches); media.addEventListener('change', sync); return () => media.removeEventListener('change', sync); }, []);
  return reduced;
}
export function useSnapshot() {
  const [state, setState] = useState({ data: null, error: '', mode: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7000);
    let active = true;
    async function load() {
      const accept = async (response) => {
        if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('Respons data belum tersedia');
        const result = await response.json();
        if (result.contract_version !== 'dashboard-alpha-1' || !Array.isArray(result.rows) || !result.rows.length || !Array.isArray(result.meta?.periods) || !result.meta.periods.length || !Array.isArray(result.meta?.provinces) || !result.meta.provinces.length || !result.spatial) throw new Error('Format data tidak sesuai atau snapshot kosong');
        return result;
      };
      try {
        const data = await accept(await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/dashboard`, { signal: controller.signal, cache: 'no-store' }));
        if (active) setState({ data, error: '', mode: 'api' });
      } catch {
        if (!active) return;
        try {
          const data = await accept(await fetch('/data/dashboard-snapshot.json', { cache: 'no-store' }));
          if (active) setState({ data, error: '', mode: 'snapshot' });
        } catch {
          if (active) setState({ data: null, error: 'API dan snapshot lokal belum tersedia. Peta batas wilayah tetap dapat dibuka.', mode: 'error' });
        }
      } finally { clearTimeout(timer); }
    }
    load();
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [attempt]);
  return { ...state, retry: () => { setState({ data: null, error: '', mode: 'loading' }); setAttempt((value) => value + 1); } };
}
