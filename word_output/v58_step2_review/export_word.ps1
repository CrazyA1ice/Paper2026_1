$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\Quant\Desktop\Paper2026_1\word_output'
$taskReview = Join-Path $taskRoot 'v58_step2_review'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Join-Path $taskRoot '2026.10.03v58.docx'), $false, $true)
    $document.Repaginate()
    $record = [ordered]@{
        filename = '2026.10.03v58.docx'
        pages = $document.ComputeStatistics(2, $false)
        words = $document.ComputeStatistics(0, $false)
        far_east_characters = $document.ComputeStatistics(6, $false)
        abstract_words = $document.Paragraphs.Item(4).Range.ComputeStatistics(0)
    }
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v58.pdf'), 17)
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview 'word_statistics.json') -Encoding UTF8
    $record | ConvertTo-Json
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
