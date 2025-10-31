# PowerShell script to setup weekly prompt update scheduled task on Windows
# This script should be run as Administrator

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonCmd = (Get-Command python -ErrorAction SilentlyContinue) -or (Get-Command python3 -ErrorAction SilentlyContinue)

if (-not $PythonCmd) {
    Write-Host "Error: Python not found. Please install Python 3." -ForegroundColor Red
    exit 1
}

$FetchScript = Join-Path $ProjectRoot "scripts\fetch_prompts_from_internet.py"
$LogDir = Join-Path $ProjectRoot "logs"

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

$TaskName = "AIAlgoTeacher_WeeklyPromptUpdate"
$TaskDescription = "Weekly update of AI/ML prompts from internet sources"

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create scheduled task action (run Python script)
$Action = New-ScheduledTaskAction -Execute $PythonCmd.Path -Argument "`"$FetchScript`"" -WorkingDirectory $ProjectRoot

# Create scheduled task trigger (every Monday at 2 AM)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 2am

# Create scheduled task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the scheduled task
Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Trigger -Settings $Settings | Out-Null

Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task details:"
Write-Host "  Name: $TaskName"
Write-Host "  Schedule: Every Monday at 2:00 AM"
Write-Host "  Script: $FetchScript"
Write-Host ""
Write-Host "To view the task: Get-ScheduledTask -TaskName $TaskName"
Write-Host "To remove the task: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"

