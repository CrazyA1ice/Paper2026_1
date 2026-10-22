$ErrorActionPreference = 'Stop'
$reviewDir = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v72_figure_notes'
$sourceDoc = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.07v72.docx'
$reviewCopy = Join-Path $reviewDir 'render_v72.docx'
Copy-Item -LiteralPath $sourceDoc -Destination $reviewCopy
$reviewDocument = $null
$reviewWord = $null
$noSave = [object]0
try {
    $reviewWord = New-Object -ComObject Word.Application
    $reviewWord.Visible = $false
    $reviewWord.DisplayAlerts = 0
    $reviewDocument = $reviewWord.Documents.Open($reviewCopy, $false, $true, $false)
    if ($reviewDocument.FullName -ne $reviewCopy) { throw 'Unexpected document' }
    $reviewDocument.Repaginate()
    $reviewDocument.ExportAsFixedFormat((Join-Path $reviewDir 'v72_review.pdf'), 17)
    $counts = [ordered]@{words=$reviewDocument.ComputeStatistics(0,$false);characters=$reviewDocument.ComputeStatistics(3,$false);pages=$reviewDocument.ComputeStatistics(2,$false)}
    $counts | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $reviewDir 'word_counts_v72.json') -Encoding utf8
    $counts | ConvertTo-Json
} finally {
    if ($null -ne $reviewDocument) { $reviewDocument.Close([ref]$noSave) }
    if ($null -ne $reviewWord -and $reviewWord.Documents.Count -eq 0) { $reviewWord.Quit([ref]$noSave) }
}
