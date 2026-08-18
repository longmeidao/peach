param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\dist\Peach')
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$OutputPath = if ([System.IO.Path]::IsPathRooted($OutputDirectory)) {
    [System.IO.Path]::GetFullPath($OutputDirectory)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputDirectory))
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Project Python not found: $Python"
}

& $Python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller is not installed in the project venv. Install it with: python -m pip install pyinstaller'
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'resources\peach.ico') -PathType Leaf)) {
    throw 'Brand assets are missing. Run scripts/generate_brand_assets.py first.'
}

$BuildPath = Join-Path $ProjectRoot 'build\windows'
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --name Peach `
    --distpath $OutputPath --workpath (Join-Path $BuildPath 'app') --specpath $BuildPath `
    --icon (Join-Path $ProjectRoot 'resources\peach.ico') `
    --add-data "$(Join-Path $ProjectRoot 'web');web" `
    --add-data "$(Join-Path $ProjectRoot 'migrations');migrations" `
    --add-data "$(Join-Path $ProjectRoot 'resources');resources" `
    (Join-Path $ProjectRoot 'scripts\build_app_entry.py')
if ($LASTEXITCODE -ne 0) { throw 'Peach build failed.' }

[pscustomobject]@{
    Executable = Join-Path $OutputPath 'Peach.exe'
    Icon = Join-Path $ProjectRoot 'resources\peach.ico'
}
