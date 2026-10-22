$ErrorActionPreference = 'Stop'
$qaDir = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v75_aigc'
$sourceDoc = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.07v75.docx'
$qaCopy = Join-Path $qaDir 'render_v75.docx'
Copy-Item -LiteralPath $sourceDoc -Destination $qaCopy
$qaDocument = $null
$qaWord = $null
$noSave = [object]0
try {
    $qaWord = New-Object -ComObject Word.Application
    $qaWord.Visible = $false
    $qaWord.DisplayAlerts = 0
    $qaDocument = $qaWord.Documents.Open($qaCopy, $false, $true, $false)
    if ($qaDocument.FullName -ne $qaCopy) { throw 'Unexpected document' }
    $qaDocument.Repaginate()
    $qaDocument.ExportAsFixedFormat((Join-Path $qaDir 'v75_review.pdf'), 17)
    $counts = [ordered]@{words=$qaDocument.ComputeStatistics(0,$false);characters=$qaDocument.ComputeStatistics(3,$false);pages=$qaDocument.ComputeStatistics(2,$false)}
    $counts | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaDir 'word_counts.json') -Encoding utf8
    $counts | ConvertTo-Json
} finally {
    if ($null -ne $qaDocument) { $qaDocument.Close([ref]$noSave) }
    if ($null -ne $qaWord -and $qaWord.Documents.Count -eq 0) { $qaWord.Quit([ref]$noSave) }
}
