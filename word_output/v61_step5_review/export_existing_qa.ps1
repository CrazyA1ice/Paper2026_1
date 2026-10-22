$ErrorActionPreference = 'Stop'
$taskReview = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\v61_step5_review'
$taskCopy = Join-Path $taskReview 'render_input.docx'
$word = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
$document = @($word.Documents) | Where-Object { $_.FullName -eq $taskCopy } | Select-Object -First 1
if ($null -eq $document) { throw 'The task QA copy is not open; no document changed.' }
$taskIncludeNotes = [object]$false
$taskNoSave = [object]0
try {
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document.Repaginate()
    $record = [ordered]@{
        filename = '2026.10.03v61.docx'
        pages = $document.ComputeStatistics(2, [ref]$taskIncludeNotes)
        words = $document.ComputeStatistics(0, [ref]$taskIncludeNotes)
        far_east_characters = $document.ComputeStatistics(6, [ref]$taskIncludeNotes)
    }
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReview 'v61_word_statistics.json') -Encoding UTF8
    $record | ConvertTo-Json
    Write-Output 'Exporting verified QA copy to PDF'
    $document.ExportAsFixedFormat((Join-Path $taskReview '2026.10.03v61.pdf'), 17)
} finally {
    $document.Close([ref]$taskNoSave)
    $word.Quit([ref]$taskNoSave)
}
