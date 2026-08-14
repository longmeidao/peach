# ============================================================
#  入库处理 —— 解压去伪装 → 快照 → 归类 → 转移 → 更新登记
#  用法:
#    .\rm-process.ps1 -Batch B20260812-231500          # 处理指定批次
#    .\rm-process.ps1 -All                             # 处理 Inbox 下全部批次
#    .\rm-process.ps1 -Batch xxx -WhatIfOnly           # 只预览不动文件
# ============================================================
param(
  [string]$Batch = '',
  [switch]$All,
  [switch]$WhatIfOnly,
  [int]$MaxDepth = 4
)
. "$PSScriptRoot\rm-lib.ps1"
RM-Init

$batches = @()
if($All){ $batches = @(Get-ChildItem -LiteralPath $Global:RM.Inbox -Directory | Select-Object -ExpandProperty Name) }
elseif($Batch){ $batches = @($Batch) }
else { Write-Output "需要 -Batch <ID> 或 -All"; return }

$Creators = RM-LoadCreators
RM-Log "已载入 $($Creators.Count) 位创作者用于归类"

foreach($b in $batches){
  $root = Join-Path $Global:RM.Inbox $b
  if(-not (Test-Path -LiteralPath $root)){ RM-Log "批次目录不存在: $b"; continue }
  RM-Log "════ 处理批次 $b ════" $b

  $mp = Join-Path $Global:RM.Manifest "$b.json"
  $m = if(Test-Path -LiteralPath $mp){ Get-Content -LiteralPath $mp -Raw | ConvertFrom-Json } else {
        [pscustomobject]@{ 批次ID=$b; 登记时间=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); 来源链接='(未登记)'; 解压密码=''; 指定创作者=''; 备注=''; 落地目录=$root; 状态=''; 文件=@() } }

  # ── 1. 递归解压 + 去伪装 ──────────────────────────
  for($depth=0; $depth -lt $MaxDepth; $depth++){
    $changed = $false
    foreach($f in @(Get-ChildItem -LiteralPath $root -Recurse -File)){
      $t = RM-TrueType $f.FullName
      if(RM-IsArchive $t){
        # 压缩包（含改扩展名伪装的）
        if($WhatIfOnly){ RM-Log "[预览] 会解压: $($f.Name) (真实类型 $t)" $b; continue }
        $dest = Join-Path $f.DirectoryName ([IO.Path]::GetFileNameWithoutExtension($f.Name) + "_x")
        $r = RM-Extract $f.FullName $dest $b
        if($r.ok){
          if($r.pw -and -not $m.解压密码){ $m.解压密码 = $r.pw }
          Remove-Item -LiteralPath $f.FullName -Force
          $changed = $true
        } else {
          $q = Join-Path $Global:RM.Quarantine $b
          New-Item -ItemType Directory -Force -Path $q | Out-Null
          Move-Item -LiteralPath $f.FullName -Destination (Join-Path $q $f.Name) -Force
          RM-Log "已隔离(解不开): $($f.Name)" $b
          $changed = $true
        }
      }
    }
    if(-not $changed){ break }
  }
  # 去伪装扩展名
  if(-not $WhatIfOnly){
    foreach($f in @(Get-ChildItem -LiteralPath $root -Recurse -File)){ [void](RM-Deceive $f.FullName $b) }
  }

  # ── 2. 逐个视频：快照 → 归类 → 转移 ─────────────────
  $vids = @(Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { (RM-Identify $_.FullName).isVideo })
  RM-Log "发现视频 $($vids.Count) 个" $b
  $records = @()

  foreach($v in $vids){
    # 快照
    $snapDir = Join-Path $Global:RM.Snapshot $b
    $snap = Join-Path $snapDir ($v.BaseName.Substring(0,[math]::Min(60,$v.BaseName.Length)) + '.jpg')
    if(-not $WhatIfOnly){ [void](RM-Snapshot $v.FullName $snap) }

    # 归类：登记时指定的创作者优先，其次按文件名(含所在子目录)匹配
    $rel = $v.FullName.Substring($root.Length).TrimStart('\')
    $who = if($m.指定创作者){ $m.指定创作者 } else { RM-Classify $rel $Creators }
    if(-not $who){ $who = '待识别' }

    $target = Join-Path $Global:RM.Library $who
    $dst = Join-Path $target $v.Name
    $i=1; while(Test-Path -LiteralPath $dst){ $dst = Join-Path $target ($v.BaseName + "_$i" + $v.Extension); $i++ }

    $records += [ordered]@{
      原文件名 = $v.Name
      原相对路径 = $rel
      字节 = $v.Length
      归类 = $who
      入库路径 = $dst
      快照 = $snap
      入库时间 = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    }

    if($WhatIfOnly){ RM-Log "[预览] $rel  ->  $who\" $b }
    else{
      New-Item -ItemType Directory -Force -Path $target | Out-Null
      Move-Item -LiteralPath $v.FullName -Destination $dst
      RM-Log "入库: $($v.Name)  ->  $who" $b
    }
  }

  # ── 3. 更新登记 ──────────────────────────────────
  if(-not $WhatIfOnly){
    $m.文件 = $records
    $m.状态 = "已入库 $($records.Count) 个视频"
    $m | Add-Member -NotePropertyName 处理时间 -NotePropertyValue (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -Force
    $m | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $mp -Encoding UTF8

    # 清空壳目录（只删空目录，不碰文件）
    $left = @(Get-ChildItem -LiteralPath $root -Recurse -File)
    if($left.Count -eq 0){ Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue; RM-Log "批次目录已清空" $b }
    else{ RM-Log "剩余 $($left.Count) 个非视频文件保留在 $root" $b }
  }
  RM-Log "════ 批次 $b 完成 ════" $b
}

Write-Output ""
Write-Output "下一步: .\rm-import.ps1     # 触发 Stash 扫描 + 打标 + 创作者归属"
