$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.09.25v28_fig6_realdata_preview.docx'
$directory = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\render_fig6_realdata_preview'
$target = Join-Path $directory '2026.09.25v28_fig6_realdata_preview.pdf'
New-Item -ItemType Directory -Force -Path $directory | Out-Null
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
