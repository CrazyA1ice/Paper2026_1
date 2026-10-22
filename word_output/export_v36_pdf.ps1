$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.09.27v36.docx'
$directory = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v36_render'
$target = Join-Path $directory '2026.09.27v36.pdf'
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($source, $false, $true)
    $document.SaveAs2($target, 17)
    Write-Output $target
} finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
