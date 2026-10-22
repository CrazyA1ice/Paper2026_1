$ErrorActionPreference = 'Stop'
$standaloneQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\standalone_submission_20261021'
$standaloneManifest = Get-Content -LiteralPath (Join-Path $standaloneQa 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$standaloneRender = Join-Path $standaloneQa 'render'
New-Item -Path $standaloneRender -ItemType Directory -Force | Out-Null
$standaloneWord = $null
$standaloneDoc = $null
try {
    $standaloneWord = New-Object -ComObject Word.Application
    $standaloneWord.Visible = $false
    $standaloneWord.DisplayAlerts = 0
    $standaloneWord.AutomationSecurity = 3
    $standaloneDoc = $standaloneWord.Documents.Open($standaloneManifest.output, $false, $true, $false)
    $standaloneDoc.Repaginate()
    $standalonePdf = Join-Path $standaloneRender 'review.pdf'
    $standaloneDoc.ExportAsFixedFormat($standalonePdf, 17)
    $standaloneStats = [ordered]@{
        pages = $standaloneDoc.ComputeStatistics(2, $false)
        words = $standaloneDoc.ComputeStatistics(0, $false)
        characters = $standaloneDoc.ComputeStatistics(3, $false)
        source = $standaloneManifest.output
        pdf = $standalonePdf
    }
    $standaloneStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $standaloneQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($standaloneStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $standaloneDoc) { $standaloneDoc.Close(0) }
    if ($null -ne $standaloneWord -and $standaloneWord.Documents.Count -eq 0) { $standaloneWord.Quit(0) }
}
