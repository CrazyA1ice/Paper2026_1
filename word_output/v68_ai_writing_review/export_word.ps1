$ErrorActionPreference = 'Stop'
$taskReview = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v68_ai_writing_review'
$taskSource = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.04v68.docx'
$taskCopy = Join-Path $taskReview 'render_input_com.docx'
Copy-Item -LiteralPath $taskSource -Destination $taskCopy
$document = $null
$word = $null
$taskNoSave = [object]0
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($taskCopy, $false, $true, $false)
    if ($document.FullName -ne $taskCopy) { throw 'Unexpected document; no content changed.' }
    $document.Repaginate()
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.04v68.pdf'), 17)
    Write-Output 'PDF export finished'
} finally {
    if ($null -ne $document) { $document.Close([ref]$taskNoSave) }
    if ($null -ne $word -and $word.Documents.Count -eq 0) { $word.Quit([ref]$taskNoSave) }
}
