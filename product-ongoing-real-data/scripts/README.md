# Pipeline scripts

Urutan pipeline penuh dijalankan melalui:

```powershell
python scripts\run_pipeline.py
python scripts\validate_project.py
```

Kelompok script:

- `extract_satusehat_tb.cjs`: ekstraksi ulang opsional dari dashboard publik.
- `prepare_*`: mengubah snapshot resmi menjadi tabel terstandar dan file QA.
- `build_analysis_panel.py`: panel TB–BPS tahunan untuk aplikasi.
- `build_tb_climate_project_panel.py`: panel utama provinsi-bulan.
- `run_preliminary_tb_climate_models.py`: model PPML eksploratif.
- `validate_project.py`: pemeriksaan akhir sebelum analisis atau pembagian project.

Semua script membaca `data/raw` dan menulis `data/processed` atau `results`. Jangan arahkan output ke `data/raw`.

