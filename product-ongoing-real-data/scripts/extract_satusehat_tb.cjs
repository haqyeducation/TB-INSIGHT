/** Export the public national TB time series from the official Kemenkes Tableau workbook.
 *
 * Important: the public workbook currently returns blank province/kabupaten fields.
 * This extractor therefore exports only the defensible NATIONAL daily series. It must
 * not be repurposed to label national totals as province observations.
 */
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const RAW_DIR = path.join(ROOT, 'data', 'raw', 'satusehat_tb');
const BASE_URL = 'https://dashboard.kemkes.go.id/views/DashboardTB/DashboardTB?:showVizHome=no';
const YEARS = [2023, 2024, 2025, 2026];
const INDICATORS = [
  ['suspected', 'Jumlah Terduga - Line chart'],
  ['tested', 'Jumlah Testing - Line chart'],
  ['notified', 'Notifikasi Kasus - Line chart'],
  ['treated', 'Jumlah Kasus Diobati - Line chart'],
];

async function exportOne(browser, indicator, tabLabel, year) {
  const filename = `${year}_national_${indicator}.csv`;
  const destination = path.join(RAW_DIR, filename);
  try {
    await fs.access(destination);
    return { indicator, year, status: 'cached', destination };
  } catch {}

  const page = await browser.newPage({ acceptDownloads: true });
  try {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.getByText('Download', { exact: true }).last().waitFor({ timeout: 90000 });
    await page.waitForTimeout(2500);

    // The workbook exposes its year filter as a Tableau canvas control.
    await page.mouse.click(110, 156);
    await page.waitForTimeout(400);
    await page.getByText(String(year), { exact: true }).last().click();
    await page.waitForTimeout(1800);
    await page.getByText(tabLabel, { exact: true }).click();
    await page.waitForTimeout(2800);

    await page.getByText('Download', { exact: true }).last().click();
    await page.getByText('Crosstab', { exact: true }).waitFor({ timeout: 20000 });
    await page.getByText('Crosstab', { exact: true }).click();
    await page.waitForTimeout(600);
    await page.getByText('CSV', { exact: true }).click();
    const downloadPromise = page.waitForEvent('download', { timeout: 60000 });
    await page.getByText('Download', { exact: true }).last().click();
    const download = await downloadPromise;
    await download.saveAs(destination);
    return { indicator, year, status: 'downloaded', destination };
  } finally {
    await page.close();
  }
}

async function main() {
  await fs.mkdir(RAW_DIR, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  });
  const tasks = YEARS.flatMap((year) => INDICATORS.map(([indicator, tabLabel]) => ({ indicator, tabLabel, year })));
  const results = [];
  let cursor = 0;

  async function worker() {
    while (cursor < tasks.length) {
      const task = tasks[cursor++];
      try {
        const result = await exportOne(browser, task.indicator, task.tabLabel, task.year);
        results.push(result);
        console.log(`${result.status}: ${task.year} ${task.indicator}`);
      } catch (error) {
        results.push({ ...task, status: 'error', error: String(error) });
        console.error(`error: ${task.year} ${task.indicator}: ${error}`);
      }
    }
  }

  await Promise.all(Array.from({ length: Number(process.env.TB_EXTRACT_WORKERS || 4) }, () => worker()));
  await browser.close();
  const manifest = {
    extractedAt: new Date().toISOString(),
    publisher: 'Kementerian Kesehatan RI',
    sourceSystem: 'SITB via SATUSEHAT Data public Tableau dashboard',
    baseUrl: BASE_URL,
    geographicLevel: 'national',
    provinceExportStatus: 'unavailable_public_dashboard_returns_blank_province_fields',
    results,
  };
  await fs.writeFile(path.join(RAW_DIR, 'extraction_manifest.json'), JSON.stringify(manifest, null, 2));
  if (results.some((item) => item.status === 'error')) process.exitCode = 1;
}

main();
