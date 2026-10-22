$ErrorActionPreference = 'Stop'
$taskReview = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v62_figure1_review'
$taskSource = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.03v62.docx'
$taskCopy = Join-Path $taskReview 'render_input.docx'
Copy-Item -LiteralPath $taskSource -Destination $taskCopy
$document = $null
$word = $null
$taskNoSave = [object]0
try {
    $taskProcess = Start-Process -FilePath 'C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE' -ArgumentList @('/a', '/q', '/n', ('"' + $taskCopy + '"')) -WindowStyle Hidden -PassThru
    $taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskReview 'word_pid.txt')
    Start-Sleep -Seconds 4
    Write-Output 'Binding only the task rendering copy'
    $document = [Runtime.InteropServices.Marshal]::BindToMoniker($taskCopy)
    if ($document.FullName -ne $taskCopy) { throw 'Unexpected document; no content changed.' }
    $word = $document.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    Write-Output 'Repaginating task copy'
    $document.Repaginate()
    Write-Output 'Exporting task copy to PDF'
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v62.pdf'), 17)
    Write-Output 'PDF export finished'
} finally {
    if ($null -ne $document) { $document.Close([ref]$taskNoSave) }
    if ($null -ne $word -and $word.Documents.Count -eq 0) { $word.Quit([ref]$taskNoSave) }
}
