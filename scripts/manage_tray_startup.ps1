param(
    [ValidateSet('Install', 'Uninstall', 'Status')]
    [string]$Action = 'Install'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Pythonw = Join-Path $ProjectRoot '.venv\Scripts\pythonw.exe'
$Startup = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $Startup 'Peach.lnk'

if ($Action -eq 'Uninstall') {
    if (Test-Path -LiteralPath $ShortcutPath -PathType Leaf) {
        Remove-Item -LiteralPath $ShortcutPath -Force
    }
    [pscustomobject]@{ Installed = $false; Shortcut = $ShortcutPath }
    exit 0
}

if ($Action -eq 'Status') {
    if (-not (Test-Path -LiteralPath $ShortcutPath -PathType Leaf)) {
        [pscustomobject]@{ Installed = $false; Shortcut = $ShortcutPath }
        exit 0
    }
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    [pscustomobject]@{
        Installed = $true
        Shortcut = $ShortcutPath
        Target = $Shortcut.TargetPath
        Arguments = $Shortcut.Arguments
        WorkingDirectory = $Shortcut.WorkingDirectory
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $Pythonw -PathType Leaf)) {
    throw "Project pythonw.exe not found: $Pythonw"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Pythonw
$Shortcut.Arguments = '-m peach.tray'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = 'Start Peach and show its system tray menu'
$Shortcut.IconLocation = "$Pythonw,0"
$Shortcut.Save()

& $PSCommandPath -Action Status
