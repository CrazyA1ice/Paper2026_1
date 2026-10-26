$ErrorActionPreference = 'Stop'
$taskQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\abstract_compression_20261023'
$taskAudit = Get-Content -LiteralPath (Join-Path $taskQa 'audit.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskRender = Join-Path $taskQa 'render_submission'
New-Item -Path $taskRender -ItemType Directory -Force | Out-Null
$taskWord = $null
$taskDoc = $null
try {
    $taskWord = New-Object -ComObject Word.Application
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    $taskDoc = $taskWord.Documents.Open($taskAudit.output, $false, $true, $false)
    $taskDoc.Repaginate()
    $taskPdf = Join-Path $taskRender 'review.pdf'
    $taskDoc.ExportAsFixedFormat($taskPdf, 17)
    $taskStats = [ordered]@{
        pages = $taskDoc.ComputeStatistics(2, $false)
        words = $taskDoc.ComputeStatistics(0, $false)
        characters = $taskDoc.ComputeStatistics(3, $false)
        shapes = $taskDoc.Shapes.Count
        sections = $taskDoc.Sections.Count
        pdf = $taskPdf
    }
    $taskStats | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskQa 'word_statistics.json') -Encoding UTF8
    Write-Output ($taskStats | ConvertTo-Json -Depth 6)
} finally {
    if ($null -ne $taskDoc) { $taskDoc.Close(0) }
    if ($null -ne $taskWord -and $taskWord.Documents.Count -eq 0) { $taskWord.Quit(0) }
}


