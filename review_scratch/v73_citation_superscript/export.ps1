$ErrorActionPreference = 'Stop'
$qaDir = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v73_citation_superscript'
$noSave = [object]0
$qaDocument = $null
$qaWord = $null
$qaCounts = @()
try {
    $qaWord = New-Object -ComObject Word.Application
    $qaWord.Visible = $false
    $qaWord.DisplayAlerts = 0
    foreach ($version in @('72','73')) {
        $sourceDoc = "C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.07v$version.docx"
        $qaCopy = Join-Path $qaDir "render_v$version.docx"
        Copy-Item -LiteralPath $sourceDoc -Destination $qaCopy
        $qaDocument = $qaWord.Documents.Open($qaCopy, $false, $true, $false)
        if ($qaDocument.FullName -ne $qaCopy) { throw 'Unexpected document' }
        $qaDocument.Repaginate()
        $qaDocument.ExportAsFixedFormat((Join-Path $qaDir "v${version}_review.pdf"), 17)
        $qaCounts += [ordered]@{version=$version;words=$qaDocument.ComputeStatistics(0,$false);characters=$qaDocument.ComputeStatistics(3,$false);pages=$qaDocument.ComputeStatistics(2,$false)}
        $qaDocument.Close([ref]$noSave)
        $qaDocument = $null
    }
    $qaCounts | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaDir 'word_counts.json') -Encoding utf8
    $qaCounts | ConvertTo-Json
} finally {
    if ($null -ne $qaDocument) { $qaDocument.Close([ref]$noSave) }
    if ($null -ne $qaWord -and $qaWord.Documents.Count -eq 0) { $qaWord.Quit([ref]$noSave) }
}
