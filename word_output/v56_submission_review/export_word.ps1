$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\Quant\Desktop\Paper2026_1\word_output'
$taskReview = Join-Path $taskRoot 'v56_submission_review'
$word = $null
$document = $null
$records = @()
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    foreach ($filename in @('2026.10.02v55.docx', '2026.10.03v56.docx')) {
        $document = $word.Documents.Open((Join-Path $taskRoot $filename), $false, $true)
        $document.Repaginate()
        $record = [ordered]@{
            filename = $filename
            pages = $document.ComputeStatistics(2, $false)
            words = $document.ComputeStatistics(0, $false)
            characters_no_spaces = $document.ComputeStatistics(3, $false)
            far_east_characters = $document.ComputeStatistics(6, $false)
        }
        if ($filename -eq '2026.10.03v56.docx') {
            $record['abstract_words'] = $document.Paragraphs.Item(4).Range.ComputeStatistics(0)
            $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v56.pdf'), 17)
        }
        $records += [pscustomobject]$record
        $document.Close($false)
        $document = $null
    }
    $records | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview 'word_statistics.json') -Encoding UTF8
    $records | ConvertTo-Json
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
