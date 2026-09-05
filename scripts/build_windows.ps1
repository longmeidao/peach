param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\dist\Peach'),
    [switch]$Standalone
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    $BuildCommonGit = (& git -C $ProjectRoot rev-parse --path-format=absolute --git-common-dir).Trim()
    $Python = Join-Path (Split-Path -Parent $BuildCommonGit) '.venv\Scripts\python.exe'
}
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

# The island bundle ships inside `--add-data web;web` and the runtime has no Node, so it
# must be rebuilt here: web/dist is committed to Git, but packaging reads the working tree,
# and a stale bundle would be shipped without any signal. See ADR-0022.
$FrontendPath = Join-Path $ProjectRoot 'frontend'
$Npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $Npm) {
    throw 'npm not found. The island bundle (frontend/) must be rebuilt before packaging; install Node 24+.'
}
& $Npm.Source --prefix $FrontendPath ci
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed in frontend/.' }
& $Npm.Source --prefix $FrontendPath run build
if ($LASTEXITCODE -ne 0) { throw 'Island bundle build failed (frontend/).' }
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'web\dist\peach-ui.js') -PathType Leaf)) {
    throw 'web/dist/peach-ui.js is missing after the frontend build.'
}

$BuildPath = Join-Path $ProjectRoot 'build\windows'
$WorkPath = Join-Path $BuildPath 'app'
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
New-Item -ItemType Directory -Path $BuildPath -Force | Out-Null

# 构建身份随包一起走：冻结的托盘读它才知道自己停在哪个提交上，检出的 HEAD 只代表源码。
$BuildInfoPath = Join-Path $BuildPath 'build-info.json'
# git 不可用、或者这份源码根本不是检出（解压出来的 tarball）时 commit 留空，构建照常。
$BuildCommit = $null
try {
    $BuildCommitText = & git -C $ProjectRoot rev-parse HEAD 2>$null
    if ($BuildCommitText) { $BuildCommit = "$BuildCommitText".Trim() }
} catch {
    $BuildCommit = $null
}
$global:LASTEXITCODE = 0
$BuildVersionMatch = Select-String -LiteralPath (Join-Path $ProjectRoot 'src\peach\__init__.py') `
    -Pattern '__version__\s*=\s*"([^"]+)"'
if (-not $BuildVersionMatch) { throw 'src/peach/__init__.py does not declare __version__.' }
$BuildInfo = [ordered]@{
    commit = $BuildCommit
    version = $BuildVersionMatch.Matches[0].Groups[1].Value
    built_at = (Get-Date).ToString('o')
}
Set-Content -LiteralPath $BuildInfoPath -Value (ConvertTo-Json $BuildInfo) -Encoding utf8

$BuildMode = @('--onefile')
$BuildDestination = $OutputPath
if ($Standalone) {
    $BuildMode = @('--onedir', '--add-data', "$(Join-Path $PSScriptRoot 'standalone.txt');.")
    $BuildDestination = Split-Path -Parent $OutputPath
}
& $Python -m PyInstaller --noconfirm --clean @BuildMode --windowed --name Peach `
    --distpath $BuildDestination --workpath $WorkPath --specpath $BuildPath `
    --paths (Join-Path $ProjectRoot 'src') --python-option 'X utf8' `
    --collect-all curl_cffi --collect-all resvg_py `
    --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan.on `
    --icon (Join-Path $ProjectRoot 'resources\peach.ico') `
    --add-data "$(Join-Path $ProjectRoot 'web');web" `
    --add-data "$(Join-Path $ProjectRoot 'migrations');migrations" `
    --add-data "$(Join-Path $ProjectRoot 'resources');resources" `
    --add-data "${BuildInfoPath};." `
    (Join-Path $ProjectRoot 'scripts\build_app_entry.py')
if ($LASTEXITCODE -ne 0) { throw 'Peach build failed.' }
if ($Standalone) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'docs/TESTING_DESKTOP.md') -Destination (Join-Path $OutputPath '开始使用.md')
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'LICENSE') -Destination (Join-Path $OutputPath 'LICENSE.txt')
}

# 工作目录只服务这一次构建：`--clean` 已让下一次不复用它，留着只是几十 MB 的中间产物。
if (Test-Path -LiteralPath $WorkPath) {
    Remove-Item -LiteralPath $WorkPath -Recurse -Force
}

[pscustomobject]@{
    Executable = Join-Path $OutputPath 'Peach.exe'
    Icon = Join-Path $ProjectRoot 'resources\peach.ico'
}
