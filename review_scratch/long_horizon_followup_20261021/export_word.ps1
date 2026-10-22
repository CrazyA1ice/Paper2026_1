$ErrorActionPreference = 'Stop'
$longRevisionQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\long_horizon_followup_20261021'
$longRevisionManifest = Get-Content -LiteralPath (Join-Path $longRevisionQa 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$longRevisionWord = $null
$longRevisionDocument = $null
$longRevisionStats = @()
try {
    $longRevisionWord = New-Object -ComObject Word.Application
    $longRevisionWord.Visible = $false
    $longRevisionWord.DisplayAlerts = 0
    $longRevisionWord.AutomationSecurity = 3
    foreach ($longRevisionKind in @('main','supplement')) {
        $longRevisionRender = Join-Path $longRevisionQa ('render_' + $longRevisionKind)
        New-Item -Path $longRevisionRender -ItemType Directory -Force | Out-Null
        $longRevisionSource = $longRevisionManifest.$longRevisionKind
        $longRevisionDocument = $longRevisionWord.Documents.Open($longRevisionSource, $false, $true, $false)
        $longRevisionDocument.Repaginate()
        $longRevisionPdf = Join-Path $longRevisionRender 'review.pdf'
        $longRevisionDocument.ExportAsFixedFormat($longRevisionPdf, 17)
        $longRevisionStats += [ordered]@{
            kind = $longRevisionKind
            pages = $longRevisionDocument.ComputeStatistics(2, $false)
            words = $longRevisionDocument.ComputeStatistics(0, $false)
            characters = $longRevisionDocument.ComputeStatistics(3, $false)
            source = $longRevisionSource
            pdf = $longRevisionPdf
        }
        $longRevisionDocument.Close(0)
        $longRevisionDocument = $null
    }
    $longRevisionStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $longRevisionQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($longRevisionStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $longRevisionDocument) { $longRevisionDocument.Close(0) }
    if ($null -ne $longRevisionWord -and $longRevisionWord.Documents.Count -eq 0) { $longRevisionWord.Quit(0) }
}
