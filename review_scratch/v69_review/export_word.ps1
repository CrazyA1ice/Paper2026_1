$ErrorActionPreference = 'Stop'
$reviewDir = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v69_review'
$sourceDoc = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.04v69.docx'
$reviewCopy = Join-Path $reviewDir 'render_input.docx'
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
    $reviewDocument.ExportAsFixedFormat((Join-Path $reviewDir 'v69_review.pdf'), 17)
    Write-Output 'PDF export finished'
} finally {
    if ($null -ne $reviewDocument) { $reviewDocument.Close([ref]$noSave) }
    if ($null -ne $reviewWord -and $reviewWord.Documents.Count -eq 0) { $reviewWord.Quit([ref]$noSave) }
}
