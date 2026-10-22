$ErrorActionPreference = 'Stop'
$paperRoot = 'C:\Users\Quant\Desktop\Paper2026_1'
$paperProject = Join-Path $paperRoot 'abilene_forecasting'
$paperQa = Join-Path $paperRoot 'review_scratch\eight_seed_unification_20261022'
$paperPython = Join-Path $paperProject '.venv\Scripts\python.exe'
$paperLogs = Join-Path $paperProject 'logs\lightts_8seeds_20261022'
$paperEvents = [System.Collections.Generic.List[object]]::new()
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class PaperSerialThermalControl {
 [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
 [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr process);
 [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr process);
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool TerminateProcess(IntPtr process, uint exitCode);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr handle);
}
'@

function Get-PaperTemperature {
    $paperTemperatureText = & nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits
    if ($LASTEXITCODE -ne 0) { throw 'Temperature query failed' }
    return [int](@($paperTemperatureText)[0].Trim())
}

function Set-PaperSuspension([int[]]$PaperTargets, [bool]$PaperSuspend) {
    foreach ($paperTarget in $PaperTargets) {
        if ($null -eq (Get-Process -Id $paperTarget -ErrorAction SilentlyContinue)) { continue }
        $paperHandle = [PaperSerialThermalControl]::OpenProcess(0x0800, $false, $paperTarget)
        if ($paperHandle -eq [IntPtr]::Zero) { throw "Cannot open experiment process $paperTarget" }
        try {
            if ($PaperSuspend) { $paperStatus = [PaperSerialThermalControl]::NtSuspendProcess($paperHandle) }
            else { $paperStatus = [PaperSerialThermalControl]::NtResumeProcess($paperHandle) }
            if ($paperStatus -ne 0) { throw "Experiment process control failed: $paperTarget $paperStatus" }
        } finally { [void][PaperSerialThermalControl]::CloseHandle($paperHandle) }
    }
}

function Watch-PaperTraining([int]$PaperTrainingId, [bool]$PaperInitiallyPaused, [string]$PaperLabel) {
    if ($PaperInitiallyPaused) { Set-PaperSuspension @($PaperTrainingId) $false }
    $paperLastReport = [datetime]::MinValue
    while ($null -ne (Get-Process -Id $PaperTrainingId -ErrorAction SilentlyContinue)) {
        $paperTemperature = Get-PaperTemperature
        if (((Get-Date) - $paperLastReport).TotalSeconds -ge 30) {
            [ordered]@{label=$PaperLabel; temperature=$paperTemperature; paused=$false; mode='single task with manufacturer thermal management'; time=(Get-Date).ToString('o')} |
                ConvertTo-Json | Set-Content -LiteralPath (Join-Path $paperQa 'thermal_status.json') -Encoding UTF8
            Write-Output "$PaperLabel temperature=$paperTemperature C running serially"
            $paperLastReport = Get-Date
        }
        Start-Sleep -Seconds 5
    }
    Write-Output "$PaperLabel process completed"
}

# These IDs were verified as the two currently suspended seed-47 jobs.
# The original scheduler remains suspended so it cannot start another job.
if (-not (Test-Path -LiteralPath (Join-Path $paperProject 'results\abilene\lightts_seed47\metrics.json'))) {
    $paperPending = Get-CimInstance Win32_Process -Filter 'ProcessId = 48040'
    if ($null -eq $paperPending -or $paperPending.CommandLine -notmatch 'train\.py.*--dataset abilene.*--model lightts.*--seed 47') { throw 'Pending Abilene job identity changed' }
    Watch-PaperTraining 48040 $true 'abilene seed47'
}
if (-not (Test-Path -LiteralPath (Join-Path $paperProject 'results\geant\lightts_seed47\metrics.json'))) {
    $paperPending = Get-CimInstance Win32_Process -Filter 'ProcessId = 10288'
    if ($null -eq $paperPending -or $paperPending.CommandLine -notmatch 'train\.py.*--dataset geant.*--model lightts.*--seed 47') { throw 'Pending GEANT job identity changed' }
    Watch-PaperTraining 10288 $true 'geant seed47'
}
foreach ($paperDataset in @('abilene','geant')) {
    if (-not (Test-Path -LiteralPath (Join-Path $paperProject "results\$paperDataset\lightts_seed47\metrics.json"))) {
        throw "Recovered job has no metrics: $paperDataset seed47"
    }
}
$paperScheduler = Get-CimInstance Win32_Process -Filter 'ProcessId = 44968'
if ($null -ne $paperScheduler) {
    if ($paperScheduler.CommandLine -notmatch 'eight_seed_unification_20261022.*run_missing\.py') {
        throw 'Scheduler identity changed; refusing process termination'
    }
    $paperSchedulerHandle = [PaperSerialThermalControl]::OpenProcess(0x0001, $false, 44968)
    if ($paperSchedulerHandle -eq [IntPtr]::Zero) { throw 'Cannot open this experiment scheduler' }
    try {
        if (-not [PaperSerialThermalControl]::TerminateProcess($paperSchedulerHandle, 0)) { throw 'Cannot retire this experiment scheduler' }
    } finally { [void][PaperSerialThermalControl]::CloseHandle($paperSchedulerHandle) }
}

foreach ($paperSeed in @(48,49)) {
    foreach ($paperDataset in @('abilene','geant')) {
        $paperDestination = Join-Path $paperProject "results\$paperDataset\lightts_seed$paperSeed"
        if (Test-Path -LiteralPath $paperDestination) { throw "Refusing to overwrite $paperDestination" }
        $paperLog = Join-Path $paperLogs "${paperDataset}_lightts_seed$paperSeed.log"
        $paperErrorLog = Join-Path $paperLogs "${paperDataset}_lightts_seed$paperSeed.stderr.log"
        $paperArguments = @('-u','train.py','--dataset',$paperDataset,'--model','lightts','--seed',"$paperSeed",'--input-len','96','--pred-len','24','--epochs','50','--patience','10','--batch-size','16','--learning-rate','0.0001')
        $paperProcess = Start-Process -FilePath $paperPython -ArgumentList $paperArguments -WorkingDirectory $paperProject -WindowStyle Hidden -RedirectStandardOutput $paperLog -RedirectStandardError $paperErrorLog -PassThru
        Watch-PaperTraining $paperProcess.Id $false "$paperDataset seed$paperSeed"
        if (-not (Test-Path -LiteralPath (Join-Path $paperDestination 'metrics.json'))) { throw "Training did not complete: $paperDataset seed$paperSeed" }
    }
}
$paperManifest = Get-Content -LiteralPath (Join-Path $paperQa 'training_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($paperProperty in $paperManifest.protected_files_sha256.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath $paperProperty.Name -Algorithm SHA256).Hash.ToLower() -ne $paperProperty.Value) {
        throw "Original data/code/metrics changed: $($paperProperty.Name)"
    }
}
$paperCompleted = @()
foreach ($paperSeed in 45..49) {
    foreach ($paperDataset in @('abilene','geant')) {
        $paperMetricsPath = Join-Path $paperProject "results\$paperDataset\lightts_seed$paperSeed\metrics.json"
        $paperMetrics = Get-Content -LiteralPath $paperMetricsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (($paperMetrics.seed -ne $paperSeed) -or ($paperMetrics.dataset -ne $paperDataset) -or ($paperMetrics.epochs_max -ne 50) -or ($paperMetrics.learning_rate -ne 0.0001)) { throw 'Recovered training configuration differs' }
        $paperCompleted += [ordered]@{dataset=$paperDataset; seed=$paperSeed; metrics=$paperMetrics.test_normalized; metrics_sha256=(Get-FileHash -LiteralPath $paperMetricsPath -Algorithm SHA256).Hash.ToLower()}
    }
}
[ordered]@{new_runs=10; all_runs_completed=$true; all_protected_files_unchanged=$true; execution_recovery='serial under manufacturer thermal management as selected by user; model/training/data unchanged'; thermal_events=$paperEvents; runs=$paperCompleted} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $paperQa 'training_complete.json') -Encoding UTF8
Write-Output 'ALL TEN NEW RUNS COMPLETE; ORIGINAL DATA, CODE AND METRICS UNCHANGED'
