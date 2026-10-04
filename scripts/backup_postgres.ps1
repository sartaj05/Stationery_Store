param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory
)

$ErrorActionPreference = "Stop"
$requiredVariables = @(
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "DJANGO_MEDIA_ROOT"
)
foreach ($variableName in $requiredVariables) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($variableName))) {
        throw "Set $variableName in this process before running the backup."
    }
}

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    throw "Install the PostgreSQL client tools so pg_dump is available."
}

$mediaRoot = [System.IO.Path]::GetFullPath($env:DJANGO_MEDIA_ROOT)
if (-not (Test-Path -LiteralPath $mediaRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $mediaRoot -Force | Out-Null
}
$backupRoot = [System.IO.Path]::GetFullPath($BackupDirectory)
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmssZ")
$databaseDump = Join-Path $backupRoot "delhi-stationery-$timestamp.dump"
$mediaArchive = Join-Path $backupRoot "delhi-stationery-media-$timestamp.zip"
$previousPassword = $env:PGPASSWORD
$previousSslMode = $env:PGSSLMODE
$postgresPort = $env:POSTGRES_PORT
if ([string]::IsNullOrWhiteSpace($postgresPort)) {
    $postgresPort = "5432"
}

try {
    $env:PGPASSWORD = $env:POSTGRES_PASSWORD
    if (-not [string]::IsNullOrWhiteSpace($env:POSTGRES_SSLMODE)) {
        $env:PGSSLMODE = $env:POSTGRES_SSLMODE
    }
    $dumpArguments = @(
        "--format=custom",
        "--host=$env:POSTGRES_HOST",
        "--port=$postgresPort",
        "--username=$env:POSTGRES_USER",
        "--dbname=$env:POSTGRES_DB",
        "--file=$databaseDump"
    )
    & pg_dump @dumpArguments
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE."
    }

    Compress-Archive -Path $mediaRoot -DestinationPath $mediaArchive -Force
    Write-Output "Database and media backups created in the requested backup directory."
}
finally {
    if ($null -eq $previousPassword) {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    else {
        $env:PGPASSWORD = $previousPassword
    }
    if ($null -eq $previousSslMode) {
        Remove-Item Env:PGSSLMODE -ErrorAction SilentlyContinue
    }
    else {
        $env:PGSSLMODE = $previousSslMode
    }
}
