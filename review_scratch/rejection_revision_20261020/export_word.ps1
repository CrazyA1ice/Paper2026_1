param([switch]$ManuscriptsOnly)
$ErrorActionPreference = 'Stop'
$revisionQaRoot = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\rejection_revision_20261020'
$revisionManifest = Get-Content -LiteralPath (Join-Path $revisionQaRoot 'manifest.json') -Raw | ConvertFrom-Json
$revisionWord = $null
$revisionDocument = $null
$revisionStats = @()
try {
    $revisionWord = New-Object -ComObject Word.Application
    $revisionWord.Visible = $false
    $revisionWord.DisplayAlerts = 0
    $revisionWord.AutomationSecurity = 3
    $revisionKinds = if ($ManuscriptsOnly) { @('clean', 'marked') } else { @('clean', 'marked', 'report') }
    foreach ($revisionKind in $revisionKinds) {
        $revisionSource = $revisionManifest.$revisionKind
        $revisionRenderDirectory = Join-Path $revisionQaRoot ('render_' + $revisionKind)
        New-Item -Path $revisionRenderDirectory -ItemType Directory -Force | Out-Null
        $revisionDocument = $revisionWord.Documents.Open($revisionSource, $false, $true, $false)
        $revisionDocument.Repaginate()
        $revisionPdf = Join-Path $revisionRenderDirectory ($revisionKind + '.pdf')
        $revisionDocument.ExportAsFixedFormat($revisionPdf, 17)
        $revisionStats += [ordered]@{
            kind = $revisionKind
            words = $revisionDocument.ComputeStatistics(0, $false)
            pages = $revisionDocument.ComputeStatistics(2, $false)
            pdf = $revisionPdf
        }
        $revisionDocument.Close(0)
        $revisionDocument = $null
        Write-Output ('Rendered ' + $revisionKind)
    }
    if ($ManuscriptsOnly) {
        $revisionExistingStats = Get-Content -LiteralPath (Join-Path $revisionQaRoot 'word_statistics.json') -Raw | ConvertFrom-Json
        $revisionStats += @($revisionExistingStats | Where-Object { $_.kind -eq 'report' })
    }
    $revisionStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $revisionQaRoot 'word_statistics.json') -Encoding utf8
} finally {
    if ($null -ne $revisionDocument) { $revisionDocument.Close(0) }
    if ($null -ne $revisionWord -and $revisionWord.Documents.Count -eq 0) { $revisionWord.Quit(0) }
}
