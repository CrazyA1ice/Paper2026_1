$ErrorActionPreference = 'Stop'
$templateQa = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\template_format_20261021'
$templateFolder = 'C:\Users\Quant\Desktop\Paper2026_1\paper_template\长春工程学院学报(自然科学版)'
New-Item -Path $templateQa -ItemType Directory -Force | Out-Null
$templateWord = $null
$templateDoc = $null
$templateRecords = @()
try {
    $templateWord = New-Object -ComObject Word.Application
    $templateWord.Visible = $false
    $templateWord.DisplayAlerts = 0
    $templateWord.AutomationSecurity = 3
    foreach ($templateName in @('论文模板','投稿须知')) {
        $templateSource = Join-Path $templateFolder ($templateName + '.doc')
        $templateDoc = $templateWord.Documents.Open($templateSource, $false, $true, $false)
        $templateDoc.Repaginate()
        $templatePages = $templateDoc.ComputeStatistics(2, $false)
        $templateCopy = Join-Path $templateQa ($templateName + '.docx')
        $templatePdf = Join-Path $templateQa ($templateName + '.pdf')
        $templateDoc.SaveAs2($templateCopy, 16)
        $templateDoc.ExportAsFixedFormat($templatePdf, 17)
        $templateRecords += [ordered]@{ name=$templateName; source=$templateSource; converted=$templateCopy; pdf=$templatePdf; pages=$templatePages }
        $templateDoc.Close(0)
        $templateDoc = $null
    }
    $templateRecords | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $templateQa 'reference_manifest.json') -Encoding UTF8
    Write-Output ($templateRecords | ConvertTo-Json -Depth 6)
} finally {
    if ($null -ne $templateDoc) { $templateDoc.Close(0) }
    if ($null -ne $templateWord -and $templateWord.Documents.Count -eq 0) { $templateWord.Quit(0) }
}
