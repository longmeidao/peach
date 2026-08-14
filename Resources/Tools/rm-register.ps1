# ============================================================
#  下载登记 —— 下载「之前/当时」跑这个，把易失信息先钉住
#  用法:
#    .\rm-register.ps1 -Url "https://..." -Password "abcd" -Note "某站合集"
#    .\rm-register.ps1 -Url "..." -Creator "跳跳羊"          # 已知创作者可直接指定
# ============================================================
param(
  [Parameter(Mandatory=$true)][string]$Url,
  [string]$Password = '',
  [string]$Note = '',
  [string]$Creator = '',
  [string]$Title = '',
  [string]$Batch = ''
)
. "$PSScriptRoot\rm-lib.ps1"
RM-Init

if(-not $Batch){ $Batch = 'B' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
$dir = Join-Path $Global:RM.Inbox $Batch
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$m = [ordered]@{
  批次ID     = $Batch
  登记时间   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
  来源链接   = $Url
  页面标题   = $Title
  解压密码   = $Password
  指定创作者 = $Creator
  备注       = $Note
  落地目录   = $dir
  状态       = '已登记-待下载'
  文件       = @()
}
$mp = Join-Path $Global:RM.Manifest "$Batch.json"
$m | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $mp -Encoding UTF8

# 密码入库，供以后自动试密码
if($Password){
  $existing = @(Get-Content -LiteralPath $Global:RM.PwBook -ErrorAction SilentlyContinue)
  if($existing -notcontains $Password){ Add-Content -LiteralPath $Global:RM.PwBook -Value $Password -Encoding UTF8 }
}

RM-Log "登记批次 $Batch  来源=$Url  密码=$(if($Password){'有'}else{'无'})" $Batch
Write-Output ""
Write-Output "批次ID : $Batch"
Write-Output "落地目录: $dir     <- 把下载的文件放这里"
Write-Output "登记文件: $mp"
Write-Output ""
Write-Output "下载完成后执行:  .\rm-process.ps1 -Batch $Batch"
