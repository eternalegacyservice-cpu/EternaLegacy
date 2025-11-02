# EternaLegacy (EternaLink) - "프로 버전" 윈도우 작업 스케줄러 등록
Write-Host "Registering EternaLegacy automated tasks..." -ForegroundColor Cyan

# --- 1. 경로 설정 ---
$BasePath = "C:\Users\micro\OneDrive\Desktop\EternaLink"
$PythonExe = "$BasePath\.venv\Scripts\python.exe"

# --- 2. 시간별(Hourly) 작업 등록 ---
$TaskName_Hourly = "EternaLegacy_Hourly"
$ScriptPath_Hourly = "$BasePath\run\run_hourly_task.py"

Write-Host "Registering: $TaskName_Hourly (runs every 1 hour)"
try {
    # 실행할 동작
    $Action_Hourly = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath_Hourly -WorkingDirectory $BasePath

    # (✨ 수정) '무한 반복'을 위해 -RepetitionDuration 파라미터 자체를 "제거"
    $Trigger_Hourly = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 60)

    # 등록 설정
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable

    # 작업 등록
    Register-ScheduledTask -TaskName $TaskName_Hourly -Action $Action_Hourly -Trigger $Trigger_Hourly -Settings $Settings -User "SYSTEM" -RunLevel Highest -Force | Out-Null
    Write-Host "[OK] $TaskName_Hourly registered." -ForegroundColor Green
} catch {
    Write-Warning "[FAIL] $TaskName_Hourly registration failed: $_"
}

# --- 3. 일일(Daily) 작업 등록 ---
$TaskName_Daily = "EternaLegacy_Daily"
$ScriptPath_Daily = "$BasePath\run\run_daily_task.py"

Write-Host "Registering: $TaskName_Daily (runs daily at 3:00 AM)"
try {
    # 실행할 동작
    $Action_Daily = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath_Daily -WorkingDirectory $BasePath

    # 실행 시점 (매일 새벽 3시에 실행)
    $Trigger_Daily = New-ScheduledTaskTrigger -Daily -At 3am

    # 등록 설정
    $Settings_Daily = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable

    # 작업 등록
    Register-ScheduledTask -TaskName $TaskName_Daily -Action $Action_Daily -Trigger $Trigger_Daily -Settings $Settings_Daily -User "SYSTEM" -RunLevel Highest -Force | Out-Null
    Write-Host "[OK] $TaskName_Daily registered." -ForegroundColor Green
} catch {
    Write-Warning "[FAIL] $TaskName_Daily registration failed: $_"
}

Write-Host "All tasks registered." -ForegroundColor Cyan
