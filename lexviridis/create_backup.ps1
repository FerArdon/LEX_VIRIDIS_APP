# Script de Backup para LEX VIRIDIS
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$backupName = "LEX_VIRIDIS_BACKUP_$timestamp.zip"
$destinationFolder = "backups"

if (!(Test-Path $destinationFolder)) {
    New-Item -ItemType Directory -Path $destinationFolder
}

$sourcePath = Get-Location
$destinationPath = Join-Path $destinationFolder $backupName

Write-Host "Iniciando backup en: $destinationPath" -ForegroundColor Cyan

# Exclusiones
$exclude = @(".venv", "build", "dist", "__pycache__", ".vscode", ".git", "backups", ".tmp.driveupload", "temp_pdfs")

# Comprimir usando PowerShell
Compress-Archive -Path * -DestinationPath $destinationPath -Force

Write-Host "✅ Backup completado exitosamente: $backupName" -ForegroundColor Green
