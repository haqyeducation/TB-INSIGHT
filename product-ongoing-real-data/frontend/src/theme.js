export const COLORS = {
  mist: '#E2F5F3',
  ice: '#A4CBE3',
  cyan: '#4DD4CD',
  indigo: '#333C77',
  ink: '#001B29',
  teal: '#087F83',
  muted: '#48616F',
  border: '#C5DEDF',
};

export const SERIES_COLORS = [COLORS.indigo, COLORS.teal, '#526FAD', '#755992'];
export const SEQUENTIAL_COLORS = ['#A4CBE3', '#80B4CC', '#6691B4', '#4B6395', '#333C77'];
export const DIVERGING_COLORS = ['#333C77', '#95A4D1', '#F0F6F7', '#8BDFDB', '#087F83'];

export function valueState(value, { invalid = false, applicable = true } = {}) {
  if (!applicable) return { kind: 'not-applicable', label: 'Tidak berlaku', short: 'N/A' };
  if (invalid) return { kind: 'invalid', label: 'Belum valid', short: '—' };
  if (value == null || (typeof value === 'number' && !Number.isFinite(value))) {
    return { kind: 'missing', label: 'Belum tersedia', short: '—' };
  }
  if (value === 0) return { kind: 'zero', label: 'Nol tercatat', short: '0' };
  return { kind: 'available', label: 'Tersedia', short: null };
}
