# Security watchdog, one scheduled run (Windows PowerShell 5.1+ or PowerShell 7). Same flow as run.sh:
#   1. poll.py (no model)                    exit 0 nothing new, 2 sources failed, 10 new items
#   2. judge_command (weak model)        only on exit 10, reads prompts\judge.md, writes relevant.json
#   3. triage_command (frontier model)   only when the judge found something relevant, reads prompts\triage.md
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File run.ps1 [--inject-test] [--baseline]
# env:   SECURITY_WATCHDOG_DIR (default %USERPROFILE%\.security-watchdog), WATCHDOG_PYTHON (default: py -3, python, python3)
$ErrorActionPreference = 'Continue'

$WD = if ($env:SECURITY_WATCHDOG_DIR) { $env:SECURITY_WATCHDOG_DIR } else { Join-Path $HOME '.security-watchdog' }
$Poll = Join-Path $PSScriptRoot 'poll.py'
$Log = Join-Path $WD 'run.log'

if (-not (Test-Path -LiteralPath $WD -PathType Container)) {
    Write-Error "watchdog folder $WD does not exist; run the setup in SKILL.md first"; exit 1
}

# find Python (the Microsoft Store 'python' stub prints a message instead of running, so check the version)
$Py = @()
if ($env:WATCHDOG_PYTHON) { $Py = @($env:WATCHDOG_PYTHON) }
else {
    foreach ($candText in @('py -3', 'python', 'python3')) {
        $cand = @($candText -split ' ')
        if (Get-Command $cand[0] -ErrorAction SilentlyContinue) {
            $exe = $cand[0]; $pre = @($cand | Select-Object -Skip 1)
            $v = & $exe @pre -c 'import sys; print(sys.version_info >= (3, 9))' 2>$null
            if ($v -eq 'True') { $Py = $cand; break }
        }
    }
}
if ($Py.Count -eq 0) { Write-Error 'Python 3.9+ not found; set WATCHDOG_PYTHON'; exit 1 }
$PyExe = $Py[0]; $PyPre = @($Py | Select-Object -Skip 1)
function Invoke-Poll {   # returns only the exit code; output goes to the log
    param([string[]]$PollArgs)
    & $PyExe @PyPre $Poll $WD @PollArgs 2>&1 | ForEach-Object { Add-Content -LiteralPath $Log -Value "$_" -Encoding UTF8 }
    return $LASTEXITCODE
}

if ((Test-Path -LiteralPath $Log) -and ((Get-Item -LiteralPath $Log).Length -gt 1MB)) {
    Move-Item -LiteralPath $Log -Destination "$Log.1" -Force
}
function Write-Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'), $msg
    Write-Output $line; Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
}

# one run at a time; a lock older than 3 hours is from a crashed run
$Lock = Join-Path $WD '.lock'
if (Test-Path -LiteralPath $Lock) {
    if ((Get-Item -LiteralPath $Lock).LastWriteTime -lt (Get-Date).AddHours(-3)) {
        Remove-Item -LiteralPath $Lock -Recurse -Force; Write-Log 'removed stale lock'
    } else { Write-Log 'another run is in progress; skipping'; exit 0 }
}
try { New-Item -ItemType Directory -Path $Lock -ErrorAction Stop | Out-Null } catch { Write-Log 'could not take the lock; skipping'; exit 0 }

function Invoke-Model([string]$Step) {
    $t = (& $PyExe @PyPre $Poll $WD --get "${Step}_timeout_minutes" | Out-String).Trim()
    if (-not $t) { $t = '30' }
    $json = (& $PyExe @PyPre $Poll $WD --print-cmd $Step --json | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $json) { Write-Log "${Step}: no ${Step}_command in config.json"; return 1 }
    $argv = @($json | ConvertFrom-Json)
    Write-Log "${Step}: starting $($argv[0]) (timeout $t min)"
    # a job runs the CLI in its own process so a hung model call can be stopped
    $job = Start-Job -ScriptBlock {
        param($dir, $exe, $rest)
        Set-Location -LiteralPath $dir
        & $exe @rest 2>&1 | ForEach-Object { "$_" }
        "__EXIT__ $LASTEXITCODE"
    } -ArgumentList $WD, $argv[0], @($argv | Select-Object -Skip 1)
    $done = Wait-Job $job -Timeout ([int]$t * 60)
    $rc = 124
    if ($done) {
        foreach ($line in (Receive-Job $job)) {
            if ("$line" -match '^__EXIT__ (-?\d+)$') { $rc = [int]$Matches[1] }
            else { Add-Content -LiteralPath $Log -Value "$line" -Encoding UTF8 }
        }
    } else { Stop-Job $job; Write-Log "${Step}: timed out" }
    Remove-Job $job -Force
    Write-Log "${Step}: exit $rc"
    return $rc
}

function Send-FailureNotice([string]$msg) {
    try { $cfg = Get-Content -LiteralPath (Join-Path $WD 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return }
    $cmd = @($cfg.notify_command)
    if ($cmd.Count -gt 0 -and $cmd[0]) {
        $msg | & $cmd[0] @($cmd | Select-Object -Skip 1) 2>&1 | ForEach-Object { Add-Content -LiteralPath $Log -Value "$_" }
    }
}

function Invoke-Triage {
    Invoke-Model 'triage' | Out-Null
    $r = Invoke-Poll @('--after-triage')
    if ($r -is [array]) { $r = $r[-1] }
    if ($r -eq 4) {
        Write-Log 'triage gave up after 3 attempts'
        Send-FailureNotice "Security watchdog: the triage step failed 3 times. Relevant items are waiting in $WD\relevant.json."
    }
}

try {
    # 0. a relevant finding from an earlier run that triage did not finish
    & $PyExe @PyPre $Poll $WD --pending-triage
    if ($LASTEXITCODE -eq 11) { Write-Log 'retrying unfinished triage'; Invoke-Triage }

    # 1. poll (no model)
    & $PyExe @PyPre $Poll $WD @args 2>&1 | ForEach-Object { Write-Log "$_" }
    $rc = $LASTEXITCODE
    if ($rc -eq 0) { exit 0 }
    if ($rc -eq 2) { Write-Log 'nothing new; some sources could not be checked (see --status)'; exit 0 }
    if ($rc -ne 10) {
        Write-Log "poll.py failed with exit $rc"
        Send-FailureNotice "Security watchdog: poll.py failed (exit $rc). See $Log."
        exit $rc
    }

    # 2. weak model judges relevance
    Invoke-Model 'judge' | Out-Null
    & $PyExe @PyPre $Poll $WD --after-judge 2>&1 | ForEach-Object { Write-Log "$_" }
    $j = $LASTEXITCODE
    if ($j -eq 11) { Invoke-Triage }          # 3. frontier model, only on a relevant item
    elseif ($j -ne 0) { Write-Log 'judge output missing or invalid; items stay pending for the next run' }
    exit 0
}
finally {
    Remove-Item -LiteralPath $Lock -Recurse -Force -ErrorAction SilentlyContinue
}
