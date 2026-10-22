$ErrorActionPreference = 'Stop'
$taskOutput = 'C:\Users\Quant\Desktop\Paper2026_1\word_output'
$taskReview = Join-Path $taskOutput 'v61_step5_review'
$word = $null
$document = $null
try {
    Write-Output 'Starting hidden Word instance'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    Write-Output 'Opening manuscript read-only'
    $document = $word.Documents.Open((Join-Path $taskOutput '2026.10.03v61.docx'), $false, $true, $false)
    Write-Output 'Repaginating manuscript'
    $document.Repaginate()
    Write-Output 'Reading document statistics'
    $record = [ordered]@{
        filename = '2026.10.03v61.docx'
        pages = $document.ComputeStatistics(2, $false)
        words = $document.ComputeStatistics(0, $false)
        far_east_characters = $document.ComputeStatistics(6, $false)
    }
    Write-Output 'Exporting PDF'
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v61.pdf'), 17)
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview 'v61_word_statistics.json') -Encoding UTF8
    $record | ConvertTo-Json
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
