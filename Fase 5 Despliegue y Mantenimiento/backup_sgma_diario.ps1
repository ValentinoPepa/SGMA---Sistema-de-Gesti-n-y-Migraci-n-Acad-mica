[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$databaseName = 'gestion_academica_v2'
$mysqlDump = 'C:\xampp\mysql\bin\mysqldump.exe'
$backupRoot = Join-Path $PSScriptRoot 'dump'
$logPath = Join-Path $PSScriptRoot 'respaldo_sgma.log'

function Write-BackupLog([string]$message) {
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'), $message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
}

$temporaryDump = $null
try {
    if (-not (Test-Path -LiteralPath $mysqlDump -PathType Leaf)) {
        throw "No se encontró mysqldump.exe en $mysqlDump"
    }

    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $finalDump = Join-Path $backupRoot "${databaseName}_${stamp}.sql"
    $temporaryDump = "$finalDump.tmp"

    $dumpArguments = @(
        '--host=127.0.0.1',
        '--port=3306',
        '--user=root',
        '--default-character-set=utf8mb4',
        '--single-transaction',
        '--quick',
        '--routines',
        '--triggers',
        '--events',
        '--hex-blob',
        "--result-file=$temporaryDump",
        $databaseName
    )

    & $mysqlDump @dumpArguments
    if ($LASTEXITCODE -ne 0) {
        throw "mysqldump terminó con código $LASTEXITCODE"
    }
    if (-not (Test-Path -LiteralPath $temporaryDump -PathType Leaf)) {
        throw 'mysqldump no generó el archivo temporal.'
    }

    $dumpInfo = Get-Item -LiteralPath $temporaryDump
    if ($dumpInfo.Length -le 0) {
        throw 'El archivo temporal de respaldo está vacío.'
    }

    Move-Item -LiteralPath $temporaryDump -Destination $finalDump
    $hash = (Get-FileHash -LiteralPath $finalDump -Algorithm SHA256).Hash
    Write-BackupLog "OK database=$databaseName file=$finalDump bytes=$($dumpInfo.Length) sha256=$hash"
    exit 0
}
catch {
    if ($temporaryDump -and (Test-Path -LiteralPath $temporaryDump -PathType Leaf)) {
        Remove-Item -LiteralPath $temporaryDump -Force -ErrorAction SilentlyContinue
    }
    Write-BackupLog "ERROR database=$databaseName message=$($_.Exception.Message)"
    exit 1
}
