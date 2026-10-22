$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.09.26v34.docx'
$directory = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\render_v34_word'
$target = Join-Path $directory '2026.09.26v34.pdf'
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$word = $null
$document = $null
try {
    Write-Output 'Starting Word'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    Write-Output 'Opening document'
    $document = $word.Documents.Open($source, $false, $true)
    Write-Output 'Saving PDF'
    $document.SaveAs2($target, 17)
    Write-Output $target
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
