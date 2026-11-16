param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,

    [Parameter(Mandatory = $true)]
    [string]$DefaultsFile,

    [string]$MySqlDumpPath = "",
    [string]$DatabaseName = "gestion_academica",
    [ValidateRange(1, 3650)]
    [int]$RetentionDays = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$backupRoot = [IO.Path]::GetFullPath($BackupDirectory)
$defaultsPath = [IO.Path]::GetFullPath($DefaultsFile)
if ($backupRoot.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "El destino del respaldo debe estar fuera de la carpeta del proyecto y de Git."
}
if ($defaultsPath.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "El archivo de credenciales debe mantenerse fuera de la carpeta del proyecto y de Git."
}
if (-not (Test-Path -LiteralPath $defaultsPath -PathType Leaf)) {
    throw "No se encuentra el archivo de opciones MySQL indicado."
}
if ([string]::IsNullOrWhiteSpace($MySqlDumpPath)) {
    $mysqldumpCommand = Get-Command mysqldump.exe -ErrorAction SilentlyContinue
    if (-not $mysqldumpCommand) {
        throw "No se encontró mysqldump.exe. Indicá su ruta en -MySqlDumpPath."
    }
    $MySqlDumpPath = $mysqldumpCommand.Source
}
if (-not (Test-Path -LiteralPath $MySqlDumpPath -PathType Leaf)) {
    throw "No se encontró mysqldump.exe en la ruta configurada."
}

New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$baseName = "${DatabaseName}_${stamp}"
$dumpPath = Join-Path $backupRoot "$baseName.sql"
$partialArchive = Join-Path $backupRoot "$baseName.sql.gz.partial"
$archivePath = Join-Path $backupRoot "$baseName.sql.gz"

try {
    # MySQL requires --defaults-extra-file to be the first client option.
    & $MySqlDumpPath "--defaults-extra-file=$defaultsPath" --single-transaction --routines --triggers --hex-blob "--result-file=$dumpPath" $DatabaseName
    if ($LASTEXITCODE -ne 0) {
        throw "mysqldump terminó con código $LASTEXITCODE. No se conservará un respaldo incompleto."
    }
    if (-not (Test-Path -LiteralPath $dumpPath -PathType Leaf) -or (Get-Item -LiteralPath $dumpPath).Length -eq 0) {
        throw "mysqldump no generó un archivo SQL válido."
    }

    $inputStream = [IO.File]::OpenRead($dumpPath)
    $outputStream = [IO.File]::Create($partialArchive)
    $gzipStream = [IO.Compression.GzipStream]::new($outputStream, [IO.Compression.CompressionLevel]::Optimal)
    try {
        $inputStream.CopyTo($gzipStream)
    }
    finally {
        $gzipStream.Dispose()
        $inputStream.Dispose()
    }
    Move-Item -LiteralPath $partialArchive -Destination $archivePath

    # Reopen the compressed file and check it contains the beginning of a SQL dump.
    $compressedStream = [IO.File]::OpenRead($archivePath)
    $decompressStream = [IO.Compression.GzipStream]::new($compressedStream, [IO.Compression.CompressionMode]::Decompress)
    $reader = [IO.StreamReader]::new($decompressStream, [Text.Encoding]::UTF8)
    try {
        $buffer = [char[]]::new(4096)
        $read = $reader.Read($buffer, 0, $buffer.Length)
        $preview = [string]::new($buffer, 0, $read)
    }
    finally {
        $reader.Dispose()
    }
    if ($read -le 0 -or $preview -notmatch "MySQL dump|CREATE TABLE|SET @OLD") {
        throw "El archivo comprimido no parece contener un dump SQL legible."
    }

    Remove-Item -LiteralPath $dumpPath -Force
    $cutoff = [DateTime]::UtcNow.AddDays(-$RetentionDays)
    Get-ChildItem -LiteralPath $backupRoot -File -Filter "${DatabaseName}_*.sql.gz" |
        Where-Object { $_.LastWriteTimeUtc -lt $cutoff } |
        Remove-Item -Force

    Write-Output "Respaldo creado y verificado: $archivePath"
    Write-Output "Retención aplicada: $RetentionDays días."
}
catch {
    Remove-Item -LiteralPath $dumpPath, $partialArchive, $archivePath -Force -ErrorAction SilentlyContinue
    throw
}
