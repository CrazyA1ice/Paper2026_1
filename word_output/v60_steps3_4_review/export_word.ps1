param([Parameter(Mandatory=$true)][string]$Revision)
$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\Quant\Desktop\Paper2026_1\word_output'
$taskReview = Join-Path $taskRoot 'v60_steps3_4_review'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $filename = '2026.10.03' + $Revision + '.docx'
    $document = $word.Documents.Open((Join-Path $taskRoot $filename), $false, $true)
    $document.Repaginate()
    $record = [ordered]@{
        filename = $filename
        pages = $document.ComputeStatistics(2, $false)
        words = $document.ComputeStatistics(0, $false)
        far_east_characters = $document.ComputeStatistics(6, $false)
    }
    $document.ExportAsFixedFormat((Join-Path $taskReview ('2026.10.03' + $Revision + '.pdf')), 17)
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview ($Revision + '_word_statistics.json')) -Encoding UTF8
    $record | ConvertTo-Json
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
