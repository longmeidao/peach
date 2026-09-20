param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$ManifestPath = Join-Path $PSScriptRoot 'cloudflared-windows.json'
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$Destination = [IO.Path]::GetFullPath($OutputPath)
$Parent = Split-Path -Parent $Destination
New-Item -ItemType Directory -Path $Parent -Force | Out-Null
$Temporary = Join-Path $Parent ('.cloudflared-' + [guid]::NewGuid().ToString('N') + '.tmp')
$Actual = $null
try {
    Invoke-WebRequest -Uri $Manifest.url -OutFile $Temporary -UseBasicParsing
    $Actual = (Get-FileHash -LiteralPath $Temporary -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Manifest.sha256.ToLowerInvariant()) {
        throw "cloudflared SHA-256 mismatch: expected $($Manifest.sha256), got $Actual"
    }
    Move-Item -LiteralPath $Temporary -Destination $Destination -Force
} finally {
    if (Test-Path -LiteralPath $Temporary) {
        Remove-Item -LiteralPath $Temporary -Force -ErrorAction SilentlyContinue
    }
}
[pscustomobject]@{ Path = $Destination; Version = $Manifest.version; SHA256 = $Actual }
