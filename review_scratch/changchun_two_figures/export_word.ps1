$ErrorActionPreference = 'Stop'
$twoFigureQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\changchun_two_figures'
$twoFigureManifest = Get-Content -LiteralPath (Join-Path $twoFigureQa 'manifest.json') -Raw | ConvertFrom-Json
$twoFigureRender = Join-Path $twoFigureQa 'render'
New-Item -Path $twoFigureRender -ItemType Directory -Force | Out-Null
$twoFigureWord = $null
$twoFigureDocument = $null
try {
    $twoFigureWord = New-Object -ComObject Word.Application
    $twoFigureWord.Visible = $false
    $twoFigureWord.DisplayAlerts = 0
    $twoFigureWord.AutomationSecurity = 3
    $twoFigureDocument = $twoFigureWord.Documents.Open($twoFigureManifest.output, $false, $true, $false)
    $twoFigureDocument.Repaginate()
    $twoFigurePdf = Join-Path $twoFigureRender 'review.pdf'
    $twoFigureDocument.ExportAsFixedFormat($twoFigurePdf, 17)
    $twoFigureStats = [ordered]@{
        pages = $twoFigureDocument.ComputeStatistics(2, $false)
        words = $twoFigureDocument.ComputeStatistics(0, $false)
        characters = $twoFigureDocument.ComputeStatistics(3, $false)
        source = $twoFigureManifest.output
        pdf = $twoFigurePdf
    }
    $twoFigureStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $twoFigureQa 'word_statistics.json') -Encoding utf8
    Write-Output ($twoFigureStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $twoFigureDocument) { $twoFigureDocument.Close(0) }
    if ($null -ne $twoFigureWord -and $twoFigureWord.Documents.Count -eq 0) { $twoFigureWord.Quit(0) }
}
