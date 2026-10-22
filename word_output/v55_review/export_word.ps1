$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.02v55.docx'
$target = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v55_review\2026.10.02v55.pdf'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($source, $false, $true)
    $document.ExportAsFixedFormat($target, 17)
    Write-Output $target
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
