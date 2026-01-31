# PowerShell Script to Configure Environment for D: Drive Installations
# Run this script as Administrator to set system-wide environment variables

Write-Host "Configuring environment to use D: drive for installations..." -ForegroundColor Green

# Create necessary directories
$directories = @(
    "D:\pip-cache",
    "D:\Python-Packages",
    "D:\Python-Packages\Lib\site-packages",
    "D:\Downloads",
    "D:\venvs",
    "D:\npm-cache",
    "D:\npm-global"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Cyan
    }
}

# Set User Environment Variables (these persist across sessions)
[System.Environment]::SetEnvironmentVariable("PIP_CACHE_DIR", "D:\pip-cache", "User")
[System.Environment]::SetEnvironmentVariable("PYTHONUSERBASE", "D:\Python-Packages", "User")
[System.Environment]::SetEnvironmentVariable("npm_config_cache", "D:\npm-cache", "User")
[System.Environment]::SetEnvironmentVariable("npm_config_prefix", "D:\npm-global", "User")

Write-Host "`nEnvironment variables set:" -ForegroundColor Green
Write-Host "  PIP_CACHE_DIR = D:\pip-cache"
Write-Host "  PYTHONUSERBASE = D:\Python-Packages"
Write-Host "  npm_config_cache = D:\npm-cache"
Write-Host "  npm_config_prefix = D:\npm-global"

# Create pip configuration file
$pipConfigDir = "$env:APPDATA\pip"
$pipConfigFile = "$pipConfigDir\pip.ini"

if (-not (Test-Path $pipConfigDir)) {
    New-Item -ItemType Directory -Path $pipConfigDir -Force | Out-Null
}

$pipConfig = @"
[global]
cache-dir = D:\pip-cache

[install]
user = true
"@

Set-Content -Path $pipConfigFile -Value $pipConfig
Write-Host "`nCreated pip config at: $pipConfigFile" -ForegroundColor Cyan

# Add D:\Python-Packages to PYTHONPATH
$currentPath = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
if ($currentPath -notlike "*D:\Python-Packages*") {
    $newPath = "D:\Python-Packages\Lib\site-packages"
    if ($currentPath) {
        $newPath = "$currentPath;$newPath"
    }
    [System.Environment]::SetEnvironmentVariable("PYTHONPATH", $newPath, "User")
    Write-Host "Added to PYTHONPATH: D:\Python-Packages\Lib\site-packages" -ForegroundColor Cyan
}

Write-Host "`n✓ Configuration complete!" -ForegroundColor Green
Write-Host "`nIMPORTANT: Restart your terminal/IDE for changes to take effect." -ForegroundColor Yellow
Write-Host "`nTo verify, run in a new terminal:" -ForegroundColor Yellow
Write-Host "  echo `$env:PIP_CACHE_DIR" -ForegroundColor Gray
Write-Host "  echo `$env:PYTHONUSERBASE" -ForegroundColor Gray
