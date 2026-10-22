$ErrorActionPreference = 'Stop'
$reviewCopy = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v69_review\render_input.docx'
$reviewWord = $null
$reviewDocument = $null
$noSave = [object]0
try {
    $reviewWord = New-Object -ComObject Word.Application
    $reviewWord.Visible = $false
    $reviewWord.DisplayAlerts = 0
    $reviewDocument = $reviewWord.Documents.Open($reviewCopy, $false, $true, $false)
    $counts = [ordered]@{words=$reviewDocument.ComputeStatistics(0,$false);characters=$reviewDocument.ComputeStatistics(3,$false);pages=$reviewDocument.ComputeStatistics(2,$false)}
    $counts | ConvertTo-Json | Set-Content -LiteralPath 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v69_review\word_counts.json' -Encoding utf8
    $counts | ConvertTo-Json
} finally {
    if ($null -ne $reviewDocument) { $reviewDocument.Close([ref]$noSave) }
    if ($null -ne $reviewWord -and $reviewWord.Documents.Count -eq 0) { $reviewWord.Quit([ref]$noSave) }
}
