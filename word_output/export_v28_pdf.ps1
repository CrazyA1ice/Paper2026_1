$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.09.23v28.docx'
$target = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\render_v28\2026.09.23v28.pdf'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $document = $word.Documents.Open($source, $false, $true)
    $document.ExportAsFixedFormat($target, 17)
    Write-Output $target
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
