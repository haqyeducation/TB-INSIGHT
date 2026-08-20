# TB-INSIGHT frontend

Dashboard React/Vite untuk data resmi TB-INSIGHT. Frontend membaca API FastAPI melalui `/api` atau `VITE_API_BASE_URL`.

```powershell
npm ci
npm run dev
```

Build produksi:

```powershell
npm run build
```

Dataset tidak disimpan di frontend. Semua data dibaca dari endpoint backend yang bersumber dari `data/processed`.
