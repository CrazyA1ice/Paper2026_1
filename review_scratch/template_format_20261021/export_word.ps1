$ErrorActionPreference = 'Stop'
$journalQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\template_format_20261021'
$journalManifest = Get-Content -LiteralPath (Join-Path $journalQa 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$journalRender = Join-Path $journalQa 'render'
New-Item -Path $journalRender -ItemType Directory -Force | Out-Null
$journalWord = $null
$journalDoc = $null
try {
    $journalWord = New-Object -ComObject Word.Application
    $journalWord.Visible = $false
    $journalWord.DisplayAlerts = 0
    $journalWord.AutomationSecurity = 3
    $journalDoc = $journalWord.Documents.Open($journalManifest.output, $false, $true, $false)
    $journalDoc.Repaginate()
    $journalPdf = Join-Path $journalRender 'review.pdf'
    $journalDoc.ExportAsFixedFormat($journalPdf, 17)
    $journalStats = [ordered]@{
        pages = $journalDoc.ComputeStatistics(2, $false)
        words = $journalDoc.ComputeStatistics(0, $false)
        characters = $journalDoc.ComputeStatistics(3, $false)
        text_boxes = $journalDoc.Shapes.Count
        sections = $journalDoc.Sections.Count
        pdf = $journalPdf
    }
    $journalStats | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $journalQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($journalStats | ConvertTo-Json -Depth 6)
} finally {
    if ($null -ne $journalDoc) { $journalDoc.Close(0) }
    if ($null -ne $journalWord -and $journalWord.Documents.Count -eq 0) { $journalWord.Quit(0) }
}
