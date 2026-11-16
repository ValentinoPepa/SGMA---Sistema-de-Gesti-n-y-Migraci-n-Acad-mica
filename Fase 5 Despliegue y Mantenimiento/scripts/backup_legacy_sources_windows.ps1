param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDirectory,

    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourceRoot = [IO.Path]::GetFullPath($SourceDirectory)
$backupRoot = [IO.Path]::GetFullPath($BackupDirectory)
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "No se encuentra la carpeta de fuentes indicada."
}
if ($backupRoot.StartsWith($sourceRoot, [StringComparison]::OrdinalIgnoreCase) -or
    $backupRoot.StartsWith($projectRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "El respaldo debe ir en una ubicación separada de las fuentes y fuera del repositorio Git."
}

$files = @(
    "Alumnos_2026_Final.xlsx",
    "Plan_Estudios.xlsx",
    "Actas_Historicas.csv",
    "Clave_Errores_Inyectados.xlsx"
)
foreach ($name in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $name) -PathType Leaf)) {
        throw "Falta uno de los archivos fuente requeridos; no se creó el respaldo."
    }
}

$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$destination = Join-Path $backupRoot "SGMA_fuentes_$stamp"
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$manifest = [Collections.Generic.List[object]]::new()

try {
    foreach ($name in $files) {
        $source = Join-Path $sourceRoot $name
        $target = Join-Path $destination $name
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        Copy-Item -LiteralPath $source -Destination $target
        $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($sourceHash -ne $targetHash) {
            throw "La verificación SHA-256 falló al copiar un archivo fuente."
        }
        $manifest.Add([pscustomobject]@{
            archivo = $name
            bytes = (Get-Item -LiteralPath $target).Length
            sha256 = $targetHash
            verificado = $true
        })
    }
    $manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $destination "manifest.json") -Encoding UTF8
}
catch {
    Remove-Item -LiteralPath $destination -Recurse -Force -ErrorAction SilentlyContinue
    throw
}

Write-Output "Respaldo verificado: $destination"
Write-Output "Archivos copiados y verificados: $($manifest.Count)"
Write-Warning "Las fuentes incluyen datos personales. Guardá el destino en un medio cifrado y con acceso restringido; no lo agregues a Git."
