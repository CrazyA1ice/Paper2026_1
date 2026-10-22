$ErrorActionPreference = 'Stop'
$simplifyQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\journal_data_simplification_20261021'
$simplifyManifest = Get-Content -LiteralPath (Join-Path $simplifyQa 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$simplifyWord = $null
$simplifyDoc = $null
$simplifyStats = @()
try {
    $simplifyWord = New-Object -ComObject Word.Application
    $simplifyWord.Visible = $false
    $simplifyWord.DisplayAlerts = 0
    $simplifyWord.AutomationSecurity = 3
    foreach ($simplifyKind in @('main','supplement')) {
        $simplifyRender = Join-Path $simplifyQa ('render_' + $simplifyKind)
        New-Item -Path $simplifyRender -ItemType Directory -Force | Out-Null
        $simplifySource = $simplifyManifest.$simplifyKind
        $simplifyDoc = $simplifyWord.Documents.Open($simplifySource, $false, $true, $false)
        $simplifyDoc.Repaginate()
        $simplifyPdf = Join-Path $simplifyRender 'review.pdf'
        $simplifyDoc.ExportAsFixedFormat($simplifyPdf, 17)
        $simplifyStats += [ordered]@{
            kind = $simplifyKind
            pages = $simplifyDoc.ComputeStatistics(2, $false)
            words = $simplifyDoc.ComputeStatistics(0, $false)
            characters = $simplifyDoc.ComputeStatistics(3, $false)
            source = $simplifySource
            pdf = $simplifyPdf
        }
        $simplifyDoc.Close(0)
        $simplifyDoc = $null
    }
    $simplifyStats | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $simplifyQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($simplifyStats | ConvertTo-Json -Depth 5)
} finally {
    if ($null -ne $simplifyDoc) { $simplifyDoc.Close(0) }
    if ($null -ne $simplifyWord -and $simplifyWord.Documents.Count -eq 0) { $simplifyWord.Quit(0) }
}
