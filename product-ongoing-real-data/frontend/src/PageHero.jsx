import { ArrowDownRight, HeartPulse } from 'lucide-react';

const PHOTOS = {
  overview: { src: '/images/health-overview.png', alt: 'Ilustrasi AI bergaya foto tenaga kesehatan dan pengunjung berkonsultasi di klinik.' },
  trend: { src: '/images/health-trends.png', alt: 'Ilustrasi AI bergaya foto dokter meninjau informasi melalui tablet di klinik.' },
  map: { src: '/images/health-maps.png', alt: 'Ilustrasi AI bergaya foto tenaga kesehatan masyarakat di lingkungan klinik.' },
};

export default function PageHero({ page, eyebrow, title, description, children }) {
  const photo = PHOTOS[page];
  return <section className={`page-hero page-hero-${page}`} aria-label={`Pengantar ${page === 'overview' ? 'ringkasan' : page === 'trend' ? 'tren' : 'peta'}`}>
    <figure className="hero-photograph"><img src={photo.src} alt={photo.alt} width="1536" height="1024" fetchPriority="high"/><figcaption>Visual ilustrasi AI · layanan kesehatan</figcaption></figure>
    <div className="hero-shade" aria-hidden="true"/>
    <div className="hero-copy"><span className="hero-kicker"><HeartPulse size={16}/>{eyebrow}</span><h1>{title}</h1><p>{description}</p>{children && <div className="hero-facts">{children}</div>}<span className="hero-reading-cue"><ArrowDownRight size={16}/>Telusuri data dan konteksnya di bawah</span></div>
  </section>;
}
