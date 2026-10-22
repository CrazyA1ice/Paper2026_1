$ErrorActionPreference = 'Stop'
$taskReview = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v61_step5_review'
$taskOriginal = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.03v61.docx'
$taskCopy = Join-Path $taskReview 'render_input.docx'
Copy-Item -LiteralPath $taskOriginal -Destination $taskCopy
$word = $null
$document = $null
$taskIncludeNotes = [object]$false
$taskNoSave = [object]0
try {
    Write-Output 'Opening QA copy with Word add-ins and Normal template disabled'
    $taskProcess = Start-Process -FilePath 'C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE' -ArgumentList @('/a', '/q', '/n', ('"' + $taskCopy + '"')) -WindowStyle Hidden -PassThru
    $taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskReview 'word_no_addins_pid.txt')
    for ($taskAttempt = 0; $taskAttempt -lt 10; $taskAttempt++) {
        Start-Sleep -Seconds 2
        try { $word = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application'); break } catch { }
    }
    if ($null -eq $word) { throw 'The task Word instance did not register its automation object.' }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = @($word.Documents) | Where-Object { $_.FullName -eq $taskCopy } | Select-Object -First 1
    if ($null -eq $document) { throw 'The QA copy is not open in the task Word instance.' }
    Write-Output 'Repaginating QA copy'
    $document.Repaginate()
    $record = [ordered]@{
        filename = '2026.10.03v61.docx'
        pages = $document.ComputeStatistics(2, [ref]$taskIncludeNotes)
        words = $document.ComputeStatistics(0, [ref]$taskIncludeNotes)
        far_east_characters = $document.ComputeStatistics(6, [ref]$taskIncludeNotes)
    }
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview 'v61_word_statistics.json') -Encoding UTF8
    $record | ConvertTo-Json
    Write-Output 'Exporting QA copy to PDF'
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v61.pdf'), 17)
} finally {
    if ($null -ne $document) { $document.Close([ref]$taskNoSave) }
    if ($null -ne $word) { $word.Quit([ref]$taskNoSave) }
}
