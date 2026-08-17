$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TrayExecutable = Join-Path $ProjectRoot 'dist\Peach\Peach.exe'
$Desktop = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $Desktop 'Peach.lnk'

if (-not (Test-Path -LiteralPath $TrayExecutable -PathType Leaf)) {
    throw "Built tray executable not found: $TrayExecutable"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TrayExecutable
$Shortcut.WorkingDirectory = Split-Path -Parent $TrayExecutable
$Shortcut.Description = 'Peach'
$Shortcut.IconLocation = "$TrayExecutable,0"
$Shortcut.WindowStyle = 7
$Shortcut.Save()

[pscustomobject]@{
    Shortcut = $ShortcutPath
    Target = $Shortcut.TargetPath
    WorkingDirectory = $Shortcut.WorkingDirectory
    Icon = $Shortcut.IconLocation
}
