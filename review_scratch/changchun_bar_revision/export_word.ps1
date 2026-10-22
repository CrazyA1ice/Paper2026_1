$ErrorActionPreference = 'Stop'
$barRevisionQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\changchun_bar_revision'
$barRevisionManifest = Get-Content -LiteralPath (Join-Path $barRevisionQa 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$barRevisionRender = Join-Path $barRevisionQa 'render'
New-Item -Path $barRevisionRender -ItemType Directory -Force | Out-Null
$barRevisionWord = $null
$barRevisionDocument = $null
try {
    $barRevisionWord = New-Object -ComObject Word.Application
    $barRevisionWord.Visible = $false
    $barRevisionWord.DisplayAlerts = 0
    $barRevisionWord.AutomationSecurity = 3
    $barRevisionDocument = $barRevisionWord.Documents.Open($barRevisionManifest.output, $false, $true, $false)
    $barRevisionDocument.Repaginate()
    $barRevisionPdf = Join-Path $barRevisionRender 'review.pdf'
    $barRevisionDocument.ExportAsFixedFormat($barRevisionPdf, 17)
    $barRevisionStats = [ordered]@{
        pages = $barRevisionDocument.ComputeStatistics(2, $false)
        words = $barRevisionDocument.ComputeStatistics(0, $false)
        characters = $barRevisionDocument.ComputeStatistics(3, $false)
        source = $barRevisionManifest.output
        pdf = $barRevisionPdf
    }
    $barRevisionStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $barRevisionQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($barRevisionStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $barRevisionDocument) { $barRevisionDocument.Close(0) }
    if ($null -ne $barRevisionWord -and $barRevisionWord.Documents.Count -eq 0) { $barRevisionWord.Quit(0) }
}
