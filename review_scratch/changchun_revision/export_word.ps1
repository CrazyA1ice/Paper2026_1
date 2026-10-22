$ErrorActionPreference = 'Stop'
$journalQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\changchun_revision'
$journalManifest = Get-Content -LiteralPath (Join-Path $journalQa 'manifest.json') -Raw | ConvertFrom-Json
$journalRenderDirectory = Join-Path $journalQa 'render'
New-Item -Path $journalRenderDirectory -ItemType Directory -Force | Out-Null
$journalWord = $null
$journalDocument = $null
try {
    $journalWord = New-Object -ComObject Word.Application
    $journalWord.Visible = $false
    $journalWord.DisplayAlerts = 0
    $journalWord.AutomationSecurity = 3
    $journalDocument = $journalWord.Documents.Open($journalManifest.output, $false, $true, $false)
    $journalDocument.Repaginate()
    $journalPdf = Join-Path $journalRenderDirectory 'review.pdf'
    $journalDocument.ExportAsFixedFormat($journalPdf, 17)
    $journalStats = [ordered]@{
        pages = $journalDocument.ComputeStatistics(2, $false)
        words = $journalDocument.ComputeStatistics(0, $false)
        characters = $journalDocument.ComputeStatistics(3, $false)
        source = $journalManifest.output
        pdf = $journalPdf
    }
    $journalStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $journalQa 'word_statistics.json') -Encoding utf8
    Write-Output ($journalStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $journalDocument) { $journalDocument.Close(0) }
    if ($null -ne $journalWord -and $journalWord.Documents.Count -eq 0) { $journalWord.Quit(0) }
}
