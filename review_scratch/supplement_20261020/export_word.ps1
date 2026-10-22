param([switch]$ManuscriptsOnly, [switch]$ReportOnly)
$ErrorActionPreference = 'Stop'
$supplementQaRoot = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\supplement_20261020'
$supplementManifest = Get-Content -LiteralPath (Join-Path $supplementQaRoot 'manifest.json') -Raw | ConvertFrom-Json
$supplementWord = $null
$supplementDocument = $null
$supplementStats = @()
try {
    $supplementWord = New-Object -ComObject Word.Application
    $supplementWord.Visible = $false
    $supplementWord.DisplayAlerts = 0
    $supplementWord.AutomationSecurity = 3
    $supplementKinds = if ($ReportOnly) { @('report') } elseif ($ManuscriptsOnly) { @('clean', 'marked') } else { @('clean', 'marked', 'report') }
    foreach ($supplementKind in $supplementKinds) {
        $supplementSource = $supplementManifest.$supplementKind
        $supplementRenderDirectory = Join-Path $supplementQaRoot ('render_' + $supplementKind)
        New-Item -Path $supplementRenderDirectory -ItemType Directory -Force | Out-Null
        $supplementDocument = $supplementWord.Documents.Open($supplementSource, $false, $true, $false)
        $supplementDocument.Repaginate()
        $supplementPdf = Join-Path $supplementRenderDirectory ($supplementKind + '.pdf')
        $supplementDocument.ExportAsFixedFormat($supplementPdf, 17)
        $supplementStats += [ordered]@{
            kind = $supplementKind
            words = $supplementDocument.ComputeStatistics(0, $false)
            pages = $supplementDocument.ComputeStatistics(2, $false)
            pdf = $supplementPdf
        }
        $supplementDocument.Close(0)
        $supplementDocument = $null
        Write-Output ('Rendered ' + $supplementKind)
    }
    if ($ReportOnly -or $ManuscriptsOnly) {
        $supplementExistingStats = Get-Content -LiteralPath (Join-Path $supplementQaRoot 'word_statistics.json') -Raw | ConvertFrom-Json
        $supplementStats += @($supplementExistingStats | Where-Object { $_.kind -notin $supplementKinds })
    }
    $supplementStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $supplementQaRoot 'word_statistics.json') -Encoding utf8
} finally {
    if ($null -ne $supplementDocument) { $supplementDocument.Close(0) }
    if ($null -ne $supplementWord -and $supplementWord.Documents.Count -eq 0) { $supplementWord.Quit(0) }
}
