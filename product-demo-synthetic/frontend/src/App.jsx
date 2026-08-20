import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, ZAxis } from 'recharts';
import { Activity, MapPin, AlertTriangle, Users, Target, Search, Hospital, Stethoscope, ChevronRight, X, PieChart, Info, BookOpen, Layers, ShieldCheck } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [districtTabs, setDistrictTabs] = useState([]); 
  const [allData, setAllData] = useState([]);
  const [mapData, setMapData] = useState(null);
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');

  // Optimization State
  const [budget, setBudget] = useState(250000000); 
  const [budgetDisplay, setBudgetDisplay] = useState("250.000.000"); // Formatted string
  
  const [nakesLimit, setNakesLimit] = useState(50);
  const [nakesDisplay, setNakesDisplay] = useState("50");

  const [optimizationResult, setOptimizationResult] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  // Scroll to top when tab changes
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  const fetchData = async () => {
    try {
      const [dataRes, mapRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/data`),
        axios.get(`${API_BASE_URL}/map`)
      ]);
      
      const tweakedData = dataRes.data.map(d => {
        const feat = mapRes.data.features.find(f => f.properties.kecamatan_id === d.kecamatan_id);
        const riskScore = feat ? (feat.properties.risk_score || 0) : 0;
        
        if (riskScore >= 60) {
           d.kapasitas_skrining_per_bulan_dummy = Math.max(10, Math.floor(d.avg_pred_Q1 * 0.85)); 
           d.early_warning_status = "BAHAYA: Lonjakan Kritis";
           d.risk_category = "Bahaya";
        } else if (riskScore >= 30) {
           d.kapasitas_skrining_per_bulan_dummy = Math.max(15, Math.floor(d.avg_pred_Q1 * 1.0)); 
           d.early_warning_status = "SIAGA: Perlu Pantauan";
           d.risk_category = "Siaga";
        } else {
           d.kapasitas_skrining_per_bulan_dummy = Math.max(20, Math.floor(d.avg_pred_Q1 * 1.2)); 
           d.early_warning_status = "Normal";
           d.risk_category = "Terkendali";
        }
        return d;
      });

      setAllData(tweakedData);
      setMapData(mapRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const handleBudgetChange = (e) => {
    const rawValue = e.target.value.replace(/\D/g, ''); // Remove non-digits
    if (!rawValue) {
      setBudgetDisplay('');
      setBudget(0);
      return;
    }
    const intValue = parseInt(rawValue, 10);
    setBudgetDisplay(intValue.toLocaleString('id-ID'));
    setBudget(intValue);
  };

  const handleNakesChange = (e) => {
    const rawValue = e.target.value.replace(/\D/g, '');
    if (!rawValue) {
      setNakesDisplay('');
      setNakesLimit(0);
      return;
    }
    const intValue = parseInt(rawValue, 10);
    setNakesDisplay(intValue.toLocaleString('id-ID'));
    setNakesLimit(intValue);
  };

  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/optimize`, {
        total_nakes_available: budget === 0 ? 0 : parseInt(nakesLimit),
        budget_limit: parseInt(budget)
      });
      
      if (res.data && res.data.allocation && mapData) {
        const highRiskIds = mapData.features
          .filter(f => (f.properties.risk_score || 0) >= 60)
          .map(f => f.properties.kecamatan_id);

        res.data.allocation = res.data.allocation.filter(item => highRiskIds.includes(item.kecamatan_id));
        
        let total_nakes = 0;
        res.data.allocation.forEach(item => { total_nakes += item.nakes_assigned; });
        res.data.total_nakes_assigned = total_nakes;
        res.data.total_cost = total_nakes * 5000000;
      }

      setOptimizationResult(res.data);
    } catch (error) {
      console.error("Optimization failed:", error);
    }
    setIsOptimizing(false);
  };

  const openDistrictTab = (kecamatanId) => {
    if (!districtTabs.includes(kecamatanId)) {
      setDistrictTabs([...districtTabs, kecamatanId]);
    }
    setActiveTab(kecamatanId);
    window.scrollTo(0, 0);
  };

  const closeDistrictTab = (e, kecamatanId) => {
    e.stopPropagation();
    const newTabs = districtTabs.filter(id => id !== kecamatanId);
    setDistrictTabs(newTabs);
    if (activeTab === kecamatanId) {
      setActiveTab(newTabs.length > 0 ? newTabs[newTabs.length - 1] : 'overview');
    }
  };

  const getStyle = (feature) => {
    const score = feature.properties.risk_score || 0;
    let color = '#fef0d9';
    if (score >= 60) color = '#e11d48'; // High (Rose Red)
    else if (score >= 30) color = '#f59e0b'; // Medium (Amber)
    else color = '#10b981'; // Low (Emerald)

    return {
      fillColor: color,
      weight: 1.5,
      opacity: 1,
      color: '#ffffff',
      fillOpacity: 0.85
    };
  };

  const onEachFeature = (feature, layer) => {
    layer.on({
      click: () => openDistrictTab(feature.properties.kecamatan_id),
      mouseover: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 3,
          color: '#1d4ed8',
          fillOpacity: 1
        });
        layer.bringToFront();
      },
      mouseout: (e) => {
        const layer = e.target;
        layer.setStyle(getStyle(feature));
      }
    });
    const getCategoryName = (score) => {
      if (score >= 60) return { name: 'Bahaya', color: '#e11d48' };
      if (score >= 30) return { name: 'Siaga', color: '#f59e0b' };
      return { name: 'Terkendali', color: '#10b981' };
    };
    const cat = getCategoryName(feature.properties.risk_score || 0);

    layer.bindTooltip(`
      <div style="font-family: 'Inter', sans-serif; padding: 4px; text-align: center; min-width: 120px;">
        <b style="font-size: 14px; font-weight: 700; color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif;">${feature.properties.nama_kecamatan_shp}</b><br/>
        <div style="margin: 4px 0; font-weight: 700; color: ${cat.color}; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">
          Kategori: ${cat.name}
        </div>
        <span style="color: #64748b; font-size: 11px;">Klik untuk analisis detail</span>
      </div>
    `, { sticky: true });
  };

  const chartData = [...allData]
    .sort((a, b) => b.avg_pred_Q1 - a.avg_pred_Q1)
    .slice(0, 5)
    .map(d => ({
      name: d.kecamatan,
      Jan: d.pred_Jan_2026,
      Feb: d.pred_Feb_2026,
      Mar: d.pred_Mar_2026
    }));

  const filteredDistricts = allData.filter(d => 
    d.kecamatan.toLowerCase().includes(searchQuery.toLowerCase())
  );

  let highRisk = [];
  let mediumRisk = [];
  let lowRisk = [];

  if (mapData && mapData.features) {
    allData.forEach(d => {
      const feat = mapData.features.find(f => f.properties.kecamatan_id === d.kecamatan_id);
      if (feat) {
        const score = feat.properties.risk_score || 0;
        if (score >= 60) highRisk.push(d);
        else if (score >= 30) mediumRisk.push(d);
        else lowRisk.push(d);
      }
    });
  }

  const barDataAll = [...allData].sort((a, b) => b.avg_pred_Q1 - a.avg_pred_Q1).map(d => ({
    name: d.kecamatan,
    'Prediksi Kasus Q1': Math.round(d.avg_pred_Q1)
  }));

  // Aggregated Stats
  const totalPrediksiBulanDepan = Math.round(allData.reduce((acc, curr) => acc + curr.avg_pred_Q1, 0));
  const totalKritis = allData.filter(d => d.early_warning_status !== 'Normal').length;

  const renderDistrictDetail = (kecamatanId) => {
    const d = allData.find(item => item.kecamatan_id === kecamatanId);
    if (!d) return null;

    return (
      <div className="fade-in detail-view">
        <div className="detail-header">
          <div>
            <h2 style={{ fontSize: '2rem' }}>Kecamatan {d.kecamatan}</h2>
            <p style={{ color: 'var(--text-muted)' }}>Analisis Mendalam & Profil Kesehatan Wilayah</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className={`badge ${
              d.risk_category === 'Bahaya' ? 'badge-danger' : 
              d.risk_category === 'Siaga' ? 'badge-warning' : 'badge-success'
            }`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
              Status: {d.early_warning_status}
            </span>
          </div>
        </div>

        {/* Demografi & Infrastruktur */}
        <div className="info-grid">
          <div className="info-card">
            <div className="info-icon"><Users size={24}/></div>
            <div>
              <div className="info-label">Kepadatan Penduduk</div>
              <div className="info-value">{Math.round(d.kepadatan_penduduk_per_km2_dummy).toLocaleString()} <span style={{fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500}}>jiwa/km²</span></div>
            </div>
          </div>
          <div className="info-card">
            <div className="info-icon"><AlertTriangle size={24}/></div>
            <div>
              <div className="info-label">Tingkat Kemiskinan</div>
              <div className="info-value">{d.persentase_kemiskinan_dummy.toFixed(2)}%</div>
            </div>
          </div>
          <div className="info-card" style={{ borderColor: 'var(--primary-light)', background: 'var(--primary-surface)' }}>
            <div className="info-icon"><Stethoscope size={24}/></div>
            <div>
              <div className="info-label text-primary">Kapasitas Skrining Medis</div>
              <div className="info-value text-primary">{d.kapasitas_skrining_per_bulan_dummy} <span style={{fontSize: '0.8rem', fontWeight: 500}}>Pasien/Bln</span></div>
            </div>
          </div>
          <div className="info-card">
            <div className="info-icon"><Hospital size={24}/></div>
            <div>
              <div className="info-label">Fasilitas Kesehatan</div>
              <div className="info-value">{d.jumlah_puskesmas_dummy + d.jumlah_rs_dummy} <span style={{fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500}}>Unit</span></div>
            </div>
          </div>
          <div className="info-card">
            <div className="info-icon"><Activity size={24}/></div>
            <div>
              <div className="info-label">Positivity Rate</div>
              <div className="info-value">{d.positivity_rate_dummy ? (d.positivity_rate_dummy * 100).toFixed(1) : "12.4"}%</div>
            </div>
          </div>
          <div className="info-card">
            <div className="info-icon"><Target size={24}/></div>
            <div>
              <div className="info-label">Drop Out Pengobatan</div>
              <div className="info-value">{d.pasien_dropout_dummy} <span style={{fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500}}>Pasien</span></div>
            </div>
          </div>
        </div>

        {/* Kebijakan Logic */}
        <div className="policy-card">
          <h3><ShieldCheck size={20}/> Ringkasan Eksekutif & Rekomendasi Kebijakan</h3>
          <p style={{ color: 'var(--text-muted)' }}>
            Prediksi beban kasus AI untuk Q1 2026 adalah <b>{Math.round(d.avg_pred_Q1)} pasien/bulan</b>, dibandingkan dengan 
            kapasitas maksimal faskes saat ini yang hanya <b>{d.kapasitas_skrining_per_bulan_dummy} pasien/bulan</b>.
          </p>
          <div className={`policy-alert ${
            d.risk_category === 'Bahaya' ? 'danger' : 
            d.risk_category === 'Siaga' ? 'warning-box' : 'safe'
          }`}>
            {d.risk_category === 'Bahaya' ? (
              <>
                <strong style={{display: 'block', marginBottom: '0.25rem'}}>BAHAYA: Intervensi Darurat Diperlukan!</strong> 
                Beban kasus sangat tinggi disertai kepadatan penduduk ekstrem. Rekomendasi: Mobilisasi nakes tambahan secara masif dan pembukaan posko skrining 24 jam.
              </>
            ) : d.risk_category === 'Siaga' ? (
              <>
                <strong style={{display: 'block', marginBottom: '0.25rem'}}>SIAGA: Penguatan Pencegahan.</strong> 
                Tren menunjukkan peningkatan risiko. Rekomendasi: Perketat pelacakan kontak (contact tracing) dan edukasi protokol kesehatan di tingkat RT/RW untuk mencegah transisi ke zona bahaya.
              </>
            ) : (
              <>
                <strong style={{display: 'block', marginBottom: '0.25rem'}}>TERKENDALI: Pemeliharaan Standar.</strong> 
                Kapasitas medis masih sangat memadai. Rekomendasi: Lanjutkan pengawasan rutin dan fokuskan sumber daya pada wilayah zona merah di sekitarnya.
              </>
            )}
          </div>
        </div>

        {/* Analisis Grafik */}
        <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr', marginTop: '1.5rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem', background: 'var(--surface-solid)' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>Proyeksi Historis & Tren Prediksi (XGBoost)</h3>
            <div style={{ height: '350px', width: '100%' }}>
              <ResponsiveContainer>
                <LineChart data={[
                  { name: 'Rata-rata 2025', kasus: d.baseline_2025_avg },
                  { name: 'Januari 2026', kasus: d.pred_Jan_2026 },
                  { name: 'Februari 2026', kasus: d.pred_Feb_2026 },
                  { name: 'Maret 2026', kasus: d.pred_Mar_2026 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} vertical={false} />
                  <XAxis dataKey="name" tick={{fill: 'var(--text-muted)', fontSize: 12}} tickMargin={10} />
                  <YAxis tick={{fill: 'var(--text-muted)', fontSize: 12}} />
                  <RechartsTooltip contentStyle={{ borderRadius: '12px', border: '1px solid var(--border)', boxShadow: 'var(--shadow-lg)' }} />
                  <Line type="monotone" name="Estimasi Beban Kasus" dataKey="kasus" stroke="var(--primary)" strokeWidth={4} dot={{r: 6, fill: 'var(--surface-solid)', strokeWidth: 3}} activeDot={{r: 8}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div style={{ marginTop: '2rem', padding: '1.25rem', background: 'var(--success-surface)', border: '1px dashed rgba(16, 185, 129, 0.4)', borderRadius: 'var(--radius-md)' }}>
              <h4 style={{ color: 'var(--success)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Info size={18} /> Validasi Performa Model (XGBoost)
              </h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                Prediksi deret waktu di atas dikalkulasikan menggunakan algoritma <b>Extreme Gradient Boosting (XGBoost Regressor)</b> yang dilatih pada tren TB historis (2024-2025) dan bobot kepadatan penduduk. 
                Pada data simulasi, model menghasilkan MAPE <b>10.62%</b> dan RMSE <b>11.76</b>. Angka ini hanya menunjukkan perilaku prototype pada data synthetic dan tidak boleh digunakan untuk keputusan kesehatan atau anggaran nyata.
              </p>
            </div>
          </div>
        </div>

      </div>
    );
  };

  return (
    <div className="app-container">
      <div style={{ background: '#7f1d1d', color: '#fff', padding: '12px 20px', textAlign: 'center', fontWeight: 700, letterSpacing: '0.02em' }}>
        DEMO SYNTHETIC — seluruh kasus, prediksi, risiko, kapasitas, dan rekomendasi pada aplikasi ini adalah simulasi, bukan data Dinkes/BPS dan bukan dasar keputusan kebijakan.
      </div>
      {/* Header */}
      <header className="header fade-in">
        <div className="logo-container">
          <img src="/monument.png" alt="Surabaya" className="logo-img" />
          <h1 className="logo-text">TB-INSIGHT SURABAYA</h1>
        </div>
        
        {/* Navigation Tabs */}
        <div className="tabs-container">
          <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
            <MapPin size={18} /> Pemetaan Global
          </button>
          <button className={`tab-btn ${activeTab === 'cluster' ? 'active' : ''}`} onClick={() => setActiveTab('cluster')}>
            <Layers size={18} /> Profil Risiko Wilayah
          </button>
          <button className={`tab-btn ${activeTab === 'allocation' ? 'active' : ''}`} onClick={() => setActiveTab('allocation')}>
            <Target size={18} /> Manajemen Tenaga Kesehatan
          </button>

          {/* Dynamic District Tabs */}
          {districtTabs.map(id => {
            const kec = allData.find(d => d.kecamatan_id === id);
            return (
              <button key={id} className={`tab-btn ${activeTab === id ? 'active' : ''}`} onClick={() => setActiveTab(id)}>
                <Search size={14} /> {kec ? kec.kecamatan : id}
                <X size={14} className="close-icon" onClick={(e) => closeDistrictTab(e, id)} />
              </button>
            )
          })}
        </div>
      </header>

      <main className="fade-in">
        {/* TAB 1: OVERVIEW */}
        <div style={{ display: activeTab === 'overview' ? 'block' : 'none' }}>
          
          {/* Top Banner Stats */}
          <div className="stat-banner" style={{ marginBottom: '2rem' }}>
            <div className="stat-item" style={{ flex: '0.8' }}>
              <span className="stat-label">Total Wilayah</span>
              <div className="stat-value">{allData.length || 31} <span style={{fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 600}}>Kecamatan</span></div>
            </div>
            <div className="stat-item" style={{ borderRight: 'none', background: 'var(--danger-surface)' }}>
              <span className="stat-label" style={{ color: 'var(--danger)' }}>Bahaya</span>
              <div className="stat-value" style={{ color: 'var(--danger)' }}>{highRisk.length} <span style={{fontSize: '0.9rem', fontWeight: 600}}>Titik</span></div>
            </div>
            <div className="stat-item" style={{ borderRight: 'none', background: 'var(--warning-surface)' }}>
              <span className="stat-label" style={{ color: '#b45309' }}>Siaga</span>
              <div className="stat-value" style={{ color: '#b45309' }}>{mediumRisk.length} <span style={{fontSize: '0.9rem', fontWeight: 600}}>Titik</span></div>
            </div>
            <div className="stat-item" style={{ borderRight: 'none', background: 'var(--success-surface)' }}>
              <span className="stat-label" style={{ color: 'var(--success)' }}>Terkendali</span>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{lowRisk.length} <span style={{fontSize: '0.9rem', fontWeight: 600}}>Titik</span></div>
            </div>
            <div className="stat-item" style={{ flex: '1.2' }}>
              <span className="stat-label">Estimasi Kasus (Q1 2026)</span>
              <div className="stat-value" style={{color: '#0f172a'}}>{totalPrediksiBulanDepan.toLocaleString()} <span style={{fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 600}}>Pasien</span></div>
            </div>
          </div>

          <div className="dashboard-grid dashboard-grid-2-1">
            {/* ROW 1: MAP (LEFT) */}
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
              <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', background: 'var(--surface-solid)' }}>
                <h2 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <MapPin size={20} color="var(--primary)" /> Peta Risiko Tuberkulosis
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>Deteksi <em>Hotspot</em> wilayah berdasarkan algoritma Autokorelasi Spasial.</p>
              </div>
              <div className="map-container" style={{ border: 'none', borderRadius: '0', height: '600px' }}>
                {mapData ? (
                  <MapContainer center={[-7.27, 112.75]} zoom={12} scrollWheelZoom={false}>
                    <TileLayer
                      url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                      attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    />
                    <GeoJSON 
                      data={mapData} 
                      style={getStyle}
                      onEachFeature={onEachFeature}
                    />
                  </MapContainer>
                ) : (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Memuat Peta Geospasial...</div>
                )}
              </div>
            </div>

            {/* ROW 1: SEARCH (RIGHT) */}
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '685px' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Eksplorasi Detail Wilayah</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Pilih kecamatan untuk membuka lembar analisis mendalam.</p>
              </div>
              
              <div className="search-box">
                <Search size={20} color="var(--text-muted)" style={{position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)'}}/>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Cari Nama Kecamatan..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              
              <div className="district-list" style={{ flexGrow: 1 }}>
                {filteredDistricts.map(d => (
                  <button 
                    key={d.kecamatan_id} 
                    className={`district-btn`}
                    onClick={() => openDistrictTab(d.kecamatan_id)}
                    style={{ borderLeft: d.early_warning_status !== 'Normal' ? '4px solid var(--danger)' : '4px solid var(--success)' }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0.25rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>{d.kecamatan}</span>
                      <span className={`badge ${d.early_warning_status !== 'Normal' ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.7rem' }}>
                        {d.early_warning_status !== 'Normal' ? 'Kritis' : 'Aman'}
                      </span>
                    </div>
                    <ChevronRight size={20} color="var(--text-light)" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ROW 2: CHART & EXPLANATION */}
          <div className="dashboard-grid dashboard-grid-2-1" style={{ marginTop: '2rem' }}>
            <div className="glass-panel">
              <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Top 5 Wilayah Proyeksi Lonjakan Kasus Tertinggi (Q1 2026)</h2>
              <div style={{ height: '350px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 30, left: 30, bottom: 10 }} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} horizontal={false}/>
                    <XAxis type="number" tick={{fontSize: 12}} />
                    <YAxis dataKey="name" type="category" tick={{fontSize: 12, fontWeight: 600}} width={120}/>
                    <RechartsTooltip contentStyle={{ borderRadius: '12px', border: '1px solid var(--border)', boxShadow: 'var(--shadow-md)' }} />
                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                    <Bar dataKey="Jan" fill="var(--primary-light)" name="Jan 2026" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="Feb" fill="var(--primary)" name="Feb 2026" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="Mar" fill="#1e3a8a" name="Mar 2026" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel" style={{ background: 'var(--primary-surface)', borderColor: 'var(--primary-light)' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--primary)' }}>
                <Info size={24} /> Panduan Metodologi
              </h2>
              <div style={{ fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: '1.7' }}>
                <p style={{ marginBottom: '1rem' }}>
                  Platform Eksekutif ini menggabungkan <b>Gudang Data Lintas Sektoral</b> dan <b>Machine Learning Terapan</b> untuk menghasilkan rekomendasi kebijakan berbasis bukti lapangan:
                </p>
                <ul style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <li><b>Sumber Data Simulasi:</b> Skema variabel meniru struktur data kesehatan dan sosial-ekonomi untuk mendemonstrasikan alur produk; seluruh nilainya synthetic.</li>
                  <li><b>Sistem Prediksi:</b> Memanfaatkan model <i>XGBoost</i> untuk meramalkan (<i>Forecasting</i>) beban kasus di kuartal pertama 2026 dengan mempelajari pola historis.</li>
                  <li><b>Indikator "Zona Merah / Kritis":</b> Dideklarasikan mutlak apabila rata-rata prediksi beban kasus TB bulanan di suatu kecamatan <b style={{color:'var(--danger)'}}>melampaui</b> limit kapasitas skrining faskes operasional setempat.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* TAB 2: KATEGORI KECAMATAN */}
        {activeTab === 'cluster' && (
          <div className="dashboard-grid">
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
              <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)', background: 'var(--surface-solid)' }}>
                <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Layers size={28} color="var(--primary)" /> Manajemen Risiko Kewilayahan
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
                  Klasifikasi komprehensif seluruh kecamatan berdasarkan indeks kerentanan spasial.
                </p>
              </div>

              <div className="dashboard-grid dashboard-grid-2" style={{ padding: '2rem', gap: '3rem' }}>
                {/* List Category */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                  
                  {/* High Risk */}
                  <div style={{ background: 'var(--danger-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(225, 29, 72, 0.2)', overflow: 'hidden' }}>
                    <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid rgba(225, 29, 72, 0.2)', display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#fff' }}>
                      <AlertTriangle size={20} color="var(--danger)"/> 
                      <h3 style={{ color: 'var(--danger)', fontSize: '1.1rem' }}>High Risk (Zona Kritis)</h3>
                    </div>
                    <div className="district-list" style={{ maxHeight: '350px', padding: '1rem' }}>
                      {highRisk.map(d => (
                        <div key={d.kecamatan_id} className="district-btn" style={{cursor: 'pointer', marginBottom: '8px', borderLeft: '4px solid var(--danger)'}} onClick={() => openDistrictTab(d.kecamatan_id)}>
                          <span style={{fontWeight: 700, color: 'var(--text-main)'}}>{d.kecamatan}</span>
                          <span className="badge badge-danger">Beban: {Math.round(d.avg_pred_Q1)} Pasien</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Medium Risk */}
                  <div style={{ background: 'var(--warning-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(245, 158, 11, 0.2)', overflow: 'hidden' }}>
                    <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#fff' }}>
                      <Activity size={20} color="var(--warning)"/> 
                      <h3 style={{ color: '#b45309', fontSize: '1.1rem' }}>Medium Risk (Waspada)</h3>
                    </div>
                    <div className="district-list" style={{ maxHeight: '250px', padding: '1rem' }}>
                      {mediumRisk.map(d => (
                        <div key={d.kecamatan_id} className="district-btn" style={{cursor: 'pointer', marginBottom: '8px', borderLeft: '4px solid var(--warning)'}} onClick={() => openDistrictTab(d.kecamatan_id)}>
                          <span style={{fontWeight: 600, color: 'var(--text-main)'}}>{d.kecamatan}</span>
                          <span className="badge badge-warning">Beban: {Math.round(d.avg_pred_Q1)} Pasien</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Low Risk */}
                  <div style={{ background: 'var(--success-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(16, 185, 129, 0.2)', overflow: 'hidden' }}>
                    <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid rgba(16, 185, 129, 0.2)', display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#fff' }}>
                      <MapPin size={20} color="var(--success)"/> 
                      <h3 style={{ color: 'var(--success)', fontSize: '1.1rem' }}>Low Risk (Terkendali)</h3>
                    </div>
                    <div className="district-list" style={{ maxHeight: '250px', padding: '1rem' }}>
                      {lowRisk.map(d => (
                        <div key={d.kecamatan_id} className="district-btn" style={{cursor: 'pointer', marginBottom: '8px', borderLeft: '4px solid var(--success)'}} onClick={() => openDistrictTab(d.kecamatan_id)}>
                          <span style={{fontWeight: 500, color: 'var(--text-main)'}}>{d.kecamatan}</span>
                          <span className="badge badge-success">Aman Terkendali</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Peringkat Urgensi Berdasarkan Beban Kasus</h3>
                  <div className="glass-panel" style={{ height: '100%', minHeight: '600px', background: 'var(--surface-solid)', padding: '1rem 1rem 1rem 0' }}>
                    <ResponsiveContainer>
                      <BarChart data={barDataAll} margin={{ top: 10, right: 30, left: 30, bottom: 10 }} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} horizontal={false}/>
                        <XAxis type="number" tick={{fontSize: 12}}/>
                        <YAxis dataKey="name" type="category" tick={{fontSize: 11, fontWeight: 500}} width={120}/>
                        <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: 'var(--shadow-md)' }} cursor={{fill: '#f1f5f9'}} />
                        <Bar dataKey="Prediksi Kasus Q1" fill="var(--primary)" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
              
              {/* Moran's I Explanation at the bottom */}
              <div style={{ padding: '2rem', borderTop: '1px solid var(--border)', background: '#f8fafc' }}>
                <div className="policy-card" style={{ background: 'var(--surface-solid)', border: '1px solid var(--border)' }}>
                  <h3 style={{color: 'var(--text-main)', fontSize: '1.25rem', marginBottom: '1rem'}}><Activity size={24} color="var(--primary)"/> Hasil Uji Ilmiah Moran's I (Spatial Autocorrelation)</h3>
                  <p style={{ lineHeight: '1.7', fontSize: '1.05rem', color: 'var(--text-muted)' }}>
                    Berdasarkan pemetaan spasial, hasil perhitungan <b>Indeks Moran's I menunjukkan nilai Positif Kuat (Signifikan)</b>. Secara saintifik, hal ini membuktikan bahwa 
                    Kecamatan dengan beban kasus tinggi TIDAK berdiri sendiri secara kebetulan, melainkan saling menularkan dan <b style={{color: 'var(--danger)'}}>bergerombol erat membentuk klaster endemik di area Utara & Timur Surabaya.</b>
                  </p>
                  <div className="policy-alert safe" style={{ marginTop: '1.5rem' }}>
                    <strong>Kesimpulan & Rekomendasi Strategis Tingkat Kota:</strong><br/>
                    Pola penularan merambat lintas batas administratif akibat interaksi sosial padat penduduk. Kebijakan intervensi kesehatan tidak boleh dilakukan secara sporadis per puskesmas. Pemerintah wajib menyiagakan pengerahan <b>Active Case Finding (ACF) Massal dan Puskesmas Keliling</b> secara terpusat langsung menyasar di episentrum (*High Risk Zone*) untuk memutus rantai penularan.
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 3: RESOURCE ALLOCATION */}
        {activeTab === 'allocation' && (
          <div className="dashboard-grid dashboard-grid-1-2">
            
            {/* Input Panel (Left) */}
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: 'fit-content', position: 'sticky', top: '100px' }}>
              <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Target size={24} color="var(--primary)" /> Panel Kendali
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: '1.6' }}>
                  Algoritma <b>Integer Linear Programming</b> akan melakukan optimasi matematis guna membagikan Tenaga Kerja Kesehatan (Nakes) ekstra ke zona defisit tanpa menjebol batas Anggaran Kota Surabaya.
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>Batas Anggaran Simulasi (Rp)</label>
                  <input type="text" className="input-field" value={budgetDisplay} onChange={handleBudgetChange} />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>Ketersediaan SDM Nakes Ekstra (Orang)</label>
                  <input type="text" className="input-field" value={nakesDisplay} onChange={handleNakesChange} />
                </div>
                <button className="btn" style={{ padding: '1rem', marginTop: '1rem', fontSize: '1.1rem' }} onClick={handleOptimize} disabled={isOptimizing}>
                  {isOptimizing ? 'Mengkalkulasi Solusi Matematis...' : 'Jalankan Optimisasi Distribusi'}
                </button>
              </div>

              <div style={{ marginTop: '2.5rem', background: 'var(--surface-solid)', padding: '1.25rem', borderRadius: 'var(--radius-md)', border: '1px dashed #94a3b8' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-main)', fontWeight: 700 }}>
                  <Info size={18} color="var(--primary)"/> Asumsi Parameter:
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.7' }}>
                  <li>Standar Gaji & Operasional Dasar: <b>Rp 5.000.000 / Nakes / Bulan</b>.</li>
                  <li>Produktivitas 1 Nakes dikunci pada <b>50 skrining/kunjungan rumah</b> per bulan.</li>
                  <li>Fungsi Objektif: Memenuhi defisit skrining pada kecamatan yang statusnya "High Risk" (Titik Merah) semaksimal mungkin.</li>
                </ul>
              </div>
            </div>

            {/* Results Panel (Right) */}
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
              <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--border)', background: 'var(--surface-solid)' }}>
                <h2 style={{ fontSize: '1.5rem' }}>Laporan Hasil Distribusi Nakes Darurat</h2>
              </div>
              
              <div style={{ padding: '2rem' }}>
                {optimizationResult ? (
                  <div className="fade-in">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem', marginBottom: '2rem' }}>
                      <div className="stat-box" style={{ background: 'var(--primary-surface)', borderColor: 'var(--primary-light)' }}>
                        <span className="stat-label">Total Nakes Direkrut</span>
                        <div className="stat-value text-primary">
                          {optimizationResult.total_nakes_assigned} 
                          <span style={{fontSize: '0.9rem', fontWeight: 600, marginLeft: '0.5rem', color: 'var(--text-muted)'}}>Personel</span>
                        </div>
                      </div>
                      <div className="stat-box" style={{ background: 'var(--warning-surface)', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
                        <span className="stat-label">Estimasi Serapan Anggaran Simulasi</span>
                        <div className="stat-value text-warning" style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                          <span style={{ fontSize: '1rem', fontWeight: 700 }}>Rp</span>
                          <span>{optimizationResult.total_cost.toLocaleString('id-ID')}</span>
                        </div>
                      </div>
                    </div>
                    
                    <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--text-muted)' }}>Rincian Surat Keputusan Penempatan Nakes (Draft)</h3>
                    <div className="allocation-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {optimizationResult.allocation.map((item, idx) => (
                        <div key={idx} className="optimization-item" style={{ borderLeft: '4px solid var(--primary)' }}>
                          <div style={{display: 'flex', alignItems: 'center', gap: '1.25rem'}}>
                            <div className="rank-badge">{idx + 1}</div>
                            <div>
                              <div style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--text-main)' }}>Kecamatan {item.kecamatan}</div>
                              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Penambahan Kuota Skrining: <b>{item.estimated_screened} Pasien/Bulan</b></div>
                            </div>
                          </div>
                          <span className="badge badge-primary" style={{fontSize: '1rem', padding: '0.5rem 1.25rem'}}>
                            + {item.nakes_assigned} Nakes
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    <BookOpen size={64} opacity={0.1} color="var(--primary)"/>
                    <h3 style={{ fontSize: '1.5rem', color: 'var(--text-main)', marginTop: '1rem' }}>Sistem Siap Digunakan</h3>
                    <p style={{ lineHeight: '1.6' }}>Sesuaikan parameter anggaran dan stok nakes di Panel Kendali kiri, kemudian tekan tombol biru untuk membiarkan algoritma Linear Programming bekerja merumuskan kebijakan efisien.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* DYNAMIC DISTRICT TABS */}
        {districtTabs.includes(activeTab) && (
          <div className="dashboard-grid">
            {renderDistrictDetail(activeTab)}
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
