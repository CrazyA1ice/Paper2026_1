$ErrorActionPreference = 'Stop'
$contentQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\figure1_table4_20261022'
$contentAudit = Get-Content -LiteralPath (Join-Path $contentQa 'audit.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$contentRender = Join-Path $contentQa 'render_final'
New-Item -Path $contentRender -ItemType Directory -Force | Out-Null
$contentWord = $null
$contentDoc = $null
try {
    $contentWord = New-Object -ComObject Word.Application
    $contentWord.Visible = $false
    $contentWord.DisplayAlerts = 0
    $contentWord.AutomationSecurity = 3
    $contentDoc = $contentWord.Documents.Open($contentAudit.output, $false, $true, $false)
    $contentDoc.Repaginate()
    $contentPdf = Join-Path $contentRender 'review.pdf'
    $contentDoc.ExportAsFixedFormat($contentPdf, 17)
    $contentStats = [ordered]@{
        pages = $contentDoc.ComputeStatistics(2, $false)
        words = $contentDoc.ComputeStatistics(0, $false)
        characters = $contentDoc.ComputeStatistics(3, $false)
        text_boxes = $contentDoc.Shapes.Count
        sections = $contentDoc.Sections.Count
        pdf = $contentPdf
    }
    $contentStats | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $contentQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($contentStats | ConvertTo-Json -Depth 6)
} finally {
    if ($null -ne $contentDoc) { $contentDoc.Close(0) }
    if ($null -ne $contentWord -and $contentWord.Documents.Count -eq 0) { $contentWord.Quit(0) }
}
