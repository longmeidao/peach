# ============================================================
#  入 Stash —— 扫描 → 关键词/元数据打标 → 创作者归属
#  用法:  .\rm-import.ps1            # 全流程
#         .\rm-import.ps1 -SkipScan  # 已扫描过，只补标签和归属
# ============================================================
param([switch]$SkipScan,[switch]$WhatIfOnly)
. "$PSScriptRoot\rm-lib.ps1"
. "$PSScriptRoot\rm-tagmap.ps1"
$u = $Global:RM.Stash

function GQ($q,$v){ $b=@{query=$q}; if($v){$b.variables=$v}
  $r=Invoke-RestMethod -Uri $u -Method Post -ContentType 'application/json' -Body ($b|ConvertTo-Json -Depth 12 -Compress)
  if($r.errors){ throw ($r.errors|ConvertTo-Json -Depth 6) }; $r.data }

# ── 1. 扫描 ──────────────────────────────────────
if(-not $SkipScan){
  RM-Log "触发 Stash 扫描..."
  $id=(GQ 'mutation{metadataScan(input:{rescan:false})}').metadataScan
  do{
    Start-Sleep -Seconds 5
    $j=(GQ '{jobQueue{id status description progress}}').jobQueue
    $me=$j | Where-Object { $_.id -eq $id }
    if($me){ RM-Log ("  扫描 {0} {1:p1}" -f $me.status,$me.progress) }
  } while($me)
  RM-Log "扫描完成"
}

# ── 2. 打标 + 归属 ───────────────────────────────
$scenes=(GQ '{findScenes(filter:{per_page:-1}){scenes{id files{path width height frame_rate duration}}}}').findScenes.scenes
RM-Log "场景总数 $($scenes.Count)"

$sceneTags=@{}
function AddT($h,$k,$v){ if(-not $h.ContainsKey($k)){$h[$k]=New-Object System.Collections.ArrayList}; [void]$h[$k].Add($v) }

foreach($s in $scenes){
  $f=$s.files[0]
  $rel=$f.path -replace '^R:\\Media\\创作者\\',''
  $top=($rel -split '\\')[0]
  $tags=New-Object System.Collections.Generic.HashSet[string]
  foreach($t in $Global:TagMap.Keys){
    foreach($kw in $Global:TagMap[$t]){ if($rel -like "*$kw*"){ [void]$tags.Add($t); break } }
  }
  if($Global:DirTags.Contains($top)){ foreach($t in $Global:DirTags[$top]){ [void]$tags.Add($t) } }
  if(-not $tags.Contains('3D动画') -and -not $tags.Contains('2D动画')){ [void]$tags.Add('真人') }

  $w=[int]$f.width; $h=[int]$f.height; $fr=[double]$f.frame_rate; $du=[double]$f.duration
  $short=[math]::Min($w,$h); $long=[math]::Max($w,$h)
  if($long -ge 3800){ [void]$tags.Add('4K') } elseif($long -ge 2500){ [void]$tags.Add('2K') }
  elseif($short -ge 1000){ [void]$tags.Add('1080P') } elseif($short -ge 700){ [void]$tags.Add('720P') }
  elseif($short -gt 0){ [void]$tags.Add('低画质') }
  if($h -gt $w){ [void]$tags.Add('竖屏') } elseif($w -gt 0){ [void]$tags.Add('横屏') }
  if($fr -ge 50){ [void]$tags.Add('高帧率') }
  if($du -gt 0){
    if($du -lt 120){ [void]$tags.Add('短片-2分内') } elseif($du -lt 600){ [void]$tags.Add('中片-10分内') }
    elseif($du -lt 1800){ [void]$tags.Add('长片-30分内') } else{ [void]$tags.Add('超长片-30分上') }
  }
  foreach($t in $tags){ AddT $sceneTags $t $s.id }
}

# 创作者归属：Performer 名+别名 子串匹配（中文名嵌在句中，autotag 匹配不到）
$perfs=(GQ '{allPerformers{id name alias_list}}').allPerformers
$scenePerf=@{}
foreach($p in $perfs){
  $keys=@(@($p.name)+@($p.alias_list) | Where-Object { $_ -and $_.Length -ge 2 })
  foreach($s in $scenes){
    $rel=$s.files[0].path -replace '^R:\\Media\\创作者\\',''
    foreach($k in $keys){ if($rel -like "*$k*"){ AddT $scenePerf $p.id $s.id; break } }
  }
}

RM-Log "标签 $($sceneTags.Count) 种 / 创作者命中 $($scenePerf.Count) 位"
if($WhatIfOnly){
  $sceneTags.GetEnumerator()|Sort-Object {$_.Value.Count} -Descending|Select-Object -First 30|ForEach-Object{ "{0,6}  {1}" -f $_.Value.Count,$_.Key }
  Write-Output "== 预览模式 =="; return
}

$existing=@{}; (GQ '{allTags{id name}}').allTags | ForEach-Object { $existing[$_.name]=$_.id }
foreach($t in $sceneTags.Keys){
  if(-not $existing.ContainsKey($t)){ $existing[$t]=(GQ 'mutation($n:String!){tagCreate(input:{name:$n}){id}}' @{n=$t}).tagCreate.id }
  $ids=@($sceneTags[$t])
  for($i=0;$i -lt $ids.Count;$i+=200){
    $b=@($ids[$i..([math]::Min($i+199,$ids.Count-1))])
    GQ 'mutation($ids:[ID!],$t:[ID!]){bulkSceneUpdate(input:{ids:$ids,tag_ids:{ids:$t,mode:ADD}}){id}}' @{ids=$b;t=@($existing[$t])} | Out-Null
  }
}
foreach($pid2 in $scenePerf.Keys){
  $ids=@($scenePerf[$pid2])
  for($i=0;$i -lt $ids.Count;$i+=200){
    $b=@($ids[$i..([math]::Min($i+199,$ids.Count-1))])
    GQ 'mutation($ids:[ID!],$p:[ID!]){bulkSceneUpdate(input:{ids:$ids,performer_ids:{ids:$p,mode:ADD}}){id}}' @{ids=$b;p=@($pid2)} | Out-Null
  }
}
RM-Log "打标与归属完成"
