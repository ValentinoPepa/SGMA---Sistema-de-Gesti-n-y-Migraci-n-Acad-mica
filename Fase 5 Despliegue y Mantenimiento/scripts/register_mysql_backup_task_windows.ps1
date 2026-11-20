param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,

    [Parameter(Mandatory = $true)]
    [string]$DefaultsFile,

    [Parameter(Mandatory = $true)]
    [string]$MySqlDumpPath,

    [string]$TaskName = "SGMA MySQL Daily Backup",

    [ValidatePattern('^([01]?\d|2[0-3]):[0-5]\d$')]
    [string]$ScheduleTime = "02:00"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$backupRoot = [IO.Path]::GetFullPath($BackupDirectory)
$defaultsPath = [IO.Path]::GetFullPath($DefaultsFile)
$dumpPath = [IO.Path]::GetFullPath($MySqlDumpPath)
$backupScript = Join-Path $PSScriptRoot "backup_mysql_windows.ps1"

if ($backupRoot.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "El destino del respaldo debe estar fuera del repositorio Git."
}
if ($defaultsPath.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "El archivo de credenciales debe estar fuera del repositorio Git."
}
foreach ($requiredPath in @($backupScript, $defaultsPath, $dumpPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "No existe un archivo requerido por la tarea programada."
    }
}

$arguments = @(
    "-NoProfile"
    "-NonInteractive"
    "-ExecutionPolicy Bypass"
    "-File `"$backupScript`""
    "-BackupDirectory `"$backupRoot`""
    "-DefaultsFile `"$defaultsPath`""
    "-MySqlDumpPath `"$dumpPath`""
    "-DatabaseName gestion_academica"
    "-RetentionDays 30"
) -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
$trigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::ParseExact($ScheduleTime, "HH:mm", $null))
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Respaldo diario local de gestion_academica; conserva 30 días." `
    -Force | Out-Null

Write-Output "Tarea registrada: $TaskName ($ScheduleTime, hora local)."
