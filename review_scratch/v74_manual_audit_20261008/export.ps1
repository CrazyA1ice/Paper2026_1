$ErrorActionPreference = 'Stop'
$qaDirectory = 'C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v74_manual_audit_20261008'
$qaSource = 'C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.07v74.docx'
$qaFinalCopy = Join-Path $qaDirectory 'render_v74_readonly.docx'
Copy-Item -LiteralPath $qaSource -Destination $qaFinalCopy
$qaDocument = $null
$qaWord = $null
$qaNoSave = [object]0

function Invoke-QaWordCall([scriptblock]$operation) {
    for ($qaAttempt = 0; $qaAttempt -lt 6; $qaAttempt++) {
        try { return (& $operation) }
        catch {
            if ($_.Exception.Message -notmatch '0x80010001|RPC_E_CALL_REJECTED' -or $qaAttempt -eq 5) { throw }
            Start-Sleep -Milliseconds 750
        }
    }
}

try {
    $qaWord = New-Object -ComObject Word.Application
    Invoke-QaWordCall { $qaWord.Visible = $false }
    Invoke-QaWordCall { $qaWord.DisplayAlerts = 0 }
    $qaDocument = Invoke-QaWordCall { $qaWord.Documents.Open($qaFinalCopy, $false, $true, $false) }
    $qaActualPath = Invoke-QaWordCall { $qaDocument.FullName }
    if ($qaActualPath -ne $qaFinalCopy) { throw 'Unexpected document path.' }
    Invoke-QaWordCall { $qaDocument.Repaginate() }
    Invoke-QaWordCall { $qaDocument.ExportAsFixedFormat((Join-Path $qaDirectory 'v74_readonly_review.pdf'), 17) }
    $qaCounts = [ordered]@{
        words = Invoke-QaWordCall { $qaDocument.ComputeStatistics(0, $false) }
        characters = Invoke-QaWordCall { $qaDocument.ComputeStatistics(3, $false) }
        pages = Invoke-QaWordCall { $qaDocument.ComputeStatistics(2, $false) }
    }
    $qaCounts | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaDirectory 'word_counts_final.json') -Encoding utf8
    $qaCounts | ConvertTo-Json
} catch {
    Write-Output ('Word export error: ' + $_.Exception.Message)
    throw
} finally {
    if ($null -ne $qaDocument) {
        try { Invoke-QaWordCall { $qaDocument.Close([ref]$qaNoSave) } }
        catch { Write-Output ('QA copy could not close: ' + $_.Exception.Message) }
    }
    if ($null -ne $qaWord) {
        try {
            $qaOpenCount = Invoke-QaWordCall { $qaWord.Documents.Count }
            if ($qaOpenCount -eq 0) { Invoke-QaWordCall { $qaWord.Quit([ref]$qaNoSave) } }
        } catch { Write-Output ('Word cleanup status: ' + $_.Exception.Message) }
    }
}

