$ErrorActionPreference = 'Stop'
$reportRoot = 'C:\Users\ACER\OneDrive\Dokumen\TB_INSIGHT'
$reportQa = Join-Path $reportRoot '.codex_tmp\s3-docx-qa'
New-Item -ItemType Directory -Force -Path $reportQa | Out-Null
$reportWord = New-Object -ComObject Word.Application
if ($reportWord.Visible -or $reportWord.Documents.Count -ne 0) {
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($reportWord)
    throw 'The conversion requires an isolated empty Word instance.'
}
try {
    $reportWord.DisplayAlerts = 0
    $reportWord.AutomationSecurity = 3
    foreach ($reportId in @('01','02')) {
        $reportName = 'S3_ERI_' + $reportId + '_Penjelasan_Perubahan'
        $reportPath = Join-Path $reportRoot ('product-ongoing-real-data\deliverables\' + $reportName + '.docx')
        $reportPdf = Join-Path $reportQa ($reportName + '.pdf')
        $reportDocument = $reportWord.Documents.Open($reportPath, $false, $true, $false)
        try {
            $reportDocument.Repaginate()
            $reportPages = $reportDocument.ComputeStatistics(2)
            $reportDocument.ExportAsFixedFormat($reportPdf, 17)
            Write-Output ($reportName + ': ' + $reportPages + ' pages')
        } finally {
            $reportDocument.Close(0)
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($reportDocument)
        }
    }
} finally {
    $reportWord.Quit(0)
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($reportWord)
}
