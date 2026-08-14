# ============================================================
#  资源管理流水线 · 公共库
#  R:\Resources\Tools\rm-lib.ps1
# ============================================================

$Global:RM = @{
  Inbox     = 'R:\Inbox'                          # 下载落地区
  Library   = 'R:\Media\创作者'                    # 媒体库
  Intake    = 'R:\Resources\Intake'                # 登记/快照/日志
  Manifest  = 'R:\Resources\Intake\manifest'
  Snapshot  = 'R:\Resources\Intake\snapshots'
  Log       = 'R:\Resources\Intake\logs'
  Quarantine= 'R:\Resources\Intake\quarantine'     # 解不开/可疑的放这里，不进库
  PwBook    = 'R:\Resources\Intake\passwords.txt'
  UnRAR     = 'C:\Program Files\WinRAR\UnRAR.exe'
  WinRAR    = 'C:\Program Files\WinRAR\WinRAR.exe'
  FFmpeg    = 'C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe'
  FFprobe   = 'C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe'
  Stash     = 'http://127.0.0.1:9999/graphql'
  VideoExt  = @('.mp4','.mkv','.mov','.avi','.m4v','.wmv','.flv','.webm','.mts','.m2ts','.ts','.mpg','.mpeg','.3gp')
}

function RM-Init {
  foreach($k in 'Inbox','Intake','Manifest','Snapshot','Log','Quarantine'){
    New-Item -ItemType Directory -Force -Path $Global:RM[$k] | Out-Null
  }
  if(-not (Test-Path -LiteralPath $Global:RM.PwBook)){
    @('# 解压密码本 —— 每行一个，# 开头为注释','# 处理时会按顺序逐个尝试') |
      Set-Content -LiteralPath $Global:RM.PwBook -Encoding UTF8
  }
}

function RM-Log { param($msg,$batch='general')
  $line="[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
  Write-Output $line
  Add-Content -LiteralPath (Join-Path $Global:RM.Log "$batch.log") -Value $line -Encoding UTF8
}

# ── 真实文件类型识别（靠 magic bytes，专治改扩展名躲审查）──────────
function RM-TrueType { param([string]$Path)
  try{ $fs=[IO.File]::OpenRead($Path) }catch{ return 'unknown' }
  $b=New-Object byte[] 16
  $n=$fs.Read($b,0,16); $fs.Close()
  if($n -lt 4){ return 'unknown' }
  $hex=($b | ForEach-Object { $_.ToString('x2') }) -join ''
  switch -Regex ($hex){
    '^504b0304|^504b0506|^504b0708' { return 'zip' }
    '^526172211a07'                 { return 'rar' }
    '^377abcaf271c'                 { return '7z' }
    '^1f8b08'                       { return 'gzip' }
    '^425a68'                       { return 'bzip2' }
    '^fd377a585a00'                 { return 'xz' }
    '^1a45dfa3'                     { return 'mkv' }
    '^464c5601'                     { return 'flv' }
    '^3026b2758e66cf11'             { return 'wmv' }
    '^000001ba|^000001b3'           { return 'mpg' }
    '^89504e470d0a1a0a'             { return 'png' }
    '^ffd8ff'                       { return 'jpg' }
    '^474946383'                    { return 'gif' }
    '^25504446'                     { return 'pdf' }
  }
  # mp4/mov 家族：偏移4处是 ftyp
  if($n -ge 12){
    $ft=[Text.Encoding]::ASCII.GetString($b,4,4)
    if($ft -eq 'ftyp'){
      $brand=[Text.Encoding]::ASCII.GetString($b,8,4)
      if($brand -match '^qt'){ return 'mov' } else { return 'mp4' }
    }
  }
  if($n -ge 12 -and [Text.Encoding]::ASCII.GetString($b,0,4) -eq 'RIFF'){
    if([Text.Encoding]::ASCII.GetString($b,8,4) -eq 'AVI '){ return 'avi' }
  }
  if([Text.Encoding]::ASCII.GetString($b,0,4) -eq '#EXT'){ return 'm3u8' }
  # MPEG-TS: 0x47 同步字节，每188字节一次
  if($b[0] -eq 0x47){ return 'ts' }
  # 裸 H.264/H.265 码流 (Annex B 起始码)
  if($hex -match '^0000000[13]'){ return 'rawes' }
  return 'unknown'
}

# ffprobe 兜底：magic bytes 认不出来时，问 ffprobe 到底是不是可播放的视频
# 专治裸码流、冷门容器、以及故意做坏文件头的伪装
function RM-ProbeVideo { param([string]$Path)
  try{
    $fmt = & $Global:RM.FFprobe -v error -show_entries format=format_name -of csv=p=0 $Path 2>$null
    $vid = & $Global:RM.FFprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 $Path 2>$null
    if($vid){ return @{ ok=$true; format="$fmt"; codec="$vid" } }
  }catch{}
  return @{ ok=$false }
}

$Global:RM_FmtExt = @{ 'mov,mp4,m4a,3gp,3g2,mj2'='.mp4'; 'matroska,webm'='.mkv'; 'avi'='.avi'
  'asf'='.wmv'; 'flv'='.flv'; 'mpegts'='.ts'; 'h264'='.h264'; 'hevc'='.h265'; 'mpeg'='.mpg' }

$Global:RM_ExtOf = @{ zip='.zip'; rar='.rar'; '7z'='.7z'; gzip='.gz'; bzip2='.bz2'; xz='.xz'
  mkv='.mkv'; mp4='.mp4'; mov='.mov'; avi='.avi'; flv='.flv'; wmv='.wmv'; mpg='.mpg'
  png='.png'; jpg='.jpg'; gif='.gif'; pdf='.pdf' }

function RM-IsArchive { param($t) return $t -in @('zip','rar','7z','gzip','bzip2','xz') }
function RM-IsVideo   { param($t) return $t -in @('mkv','mp4','mov','avi','flv','wmv','mpg','ts','rawes') }

# 综合判定：先 magic bytes，认不出且不是已知非视频类型时用 ffprobe 兜底
# 返回 @{ type=类型; ext=应有扩展名; isVideo=bool }
function RM-Identify { param([string]$Path)
  $t = RM-TrueType $Path
  if(RM-IsArchive $t){ return @{ type=$t; ext=$Global:RM_ExtOf[$t]; isVideo=$false; isArchive=$true } }
  if(RM-IsVideo $t){
    $ext = $Global:RM_ExtOf[$t]
    if(-not $ext -and $t -in @('ts','rawes')){
      $pr = RM-ProbeVideo $Path
      $ext = if($pr.ok -and $Global:RM_FmtExt[$pr.format]){ $Global:RM_FmtExt[$pr.format] } else { '.ts' }
    }
    return @{ type=$t; ext=$ext; isVideo=$true; isArchive=$false }
  }
  if($t -in @('png','jpg','gif','pdf','m3u8')){ return @{ type=$t; ext=$Global:RM_ExtOf[$t]; isVideo=$false; isArchive=$false } }
  # 未知：问 ffprobe
  $pr = RM-ProbeVideo $Path
  if($pr.ok){
    $ext = if($Global:RM_FmtExt[$pr.format]){ $Global:RM_FmtExt[$pr.format] } else { '.mp4' }
    return @{ type="probe:$($pr.format)"; ext=$ext; isVideo=$true; isArchive=$false }
  }
  return @{ type='unknown'; ext=$null; isVideo=$false; isArchive=$false }
}

# ── 去伪装：按真实类型修正扩展名 ──────────────────────────────
function RM-Deceive { param([string]$Path,[string]$Batch)
  $id=RM-Identify $Path
  $t=$id.type
  if($t -eq 'unknown'){ return $Path }
  $want=$id.ext
  if(-not $want){ return $Path }
  $cur=[IO.Path]::GetExtension($Path).ToLower()
  if($cur -eq $want){ return $Path }
  # .m4v/.ts 等合法别名不强改
  if($t -eq 'mp4' -and $cur -in @('.m4v','.mp4')){ return $Path }
  $new=[IO.Path]::ChangeExtension($Path,$want.TrimStart('.'))
  $i=1; while(Test-Path -LiteralPath $new){ $new=[IO.Path]::Combine([IO.Path]::GetDirectoryName($Path),[IO.Path]::GetFileNameWithoutExtension($Path)+"_$i"+$want); $i++ }
  Move-Item -LiteralPath $Path -Destination $new
  RM-Log "去伪装: $([IO.Path]::GetFileName($Path))  [$cur -> $want] (真实类型 $t)" $Batch
  return $new
}

# ── 解压（自动试密码），返回是否成功 ────────────────────────────
function RM-Extract { param([string]$Archive,[string]$Dest,[string]$Batch)
  New-Item -ItemType Directory -Force -Path $Dest | Out-Null
  $pws=@('')
  if(Test-Path -LiteralPath $Global:RM.PwBook){
    $pws += @(Get-Content -LiteralPath $Global:RM.PwBook | Where-Object { $_ -and -not $_.StartsWith('#') })
  }
  foreach($pw in $pws){
    $args=@('x','-y','-idq',"-p$(if($pw){$pw}else{'-'})",$Archive,"$Dest\")
    $p=Start-Process -FilePath $Global:RM.UnRAR -ArgumentList $args -NoNewWindow -Wait -PassThru
    if($p.ExitCode -eq 0){
      RM-Log "解压成功: $([IO.Path]::GetFileName($Archive))$(if($pw){" (密码: $pw)"})" $Batch
      return @{ ok=$true; pw=$pw }
    }
  }
  RM-Log "解压失败(密码未命中或损坏): $([IO.Path]::GetFileName($Archive))" $Batch
  return @{ ok=$false; pw=$null }
}

# ── 快照：抽关键帧拼接触表，作为入库视觉留档 ──────────────────
function RM-Snapshot { param([string]$Video,[string]$OutJpg,[int]$N=9)
  $d=0.0
  [double]::TryParse((& $Global:RM.FFprobe -v error -show_entries format=duration -of csv=p=0 $Video 2>$null),[ref]$d)|Out-Null
  if($d -le 2){ $d=30 }
  $tmp=Join-Path $env:TEMP ("rmsnap_"+[Guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Force -Path $tmp|Out-Null
  $W=480;$H=340
  $vf="scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:white,format=yuvj420p"
  for($k=0;$k -lt $N;$k++){
    $ts=[math]::Round($d*(0.1+0.8*$k/[math]::Max(1,$N-1)),2)
    & $Global:RM.FFmpeg -v error -y -ss $ts -i $Video -frames:v 1 -vf $vf -q:v 3 (Join-Path $tmp ("{0:d2}.jpg" -f ($k+1))) 2>$null
  }
  $cols=3;$rows=[math]::Ceiling($N/$cols)
  New-Item -ItemType Directory -Force -Path (Split-Path $OutJpg) | Out-Null
  & $Global:RM.FFmpeg -v error -y -framerate 1 -i (Join-Path $tmp '%02d.jpg') -vf "tile=${cols}x${rows}:margin=4:padding=4:color=white" -frames:v 1 -q:v 3 $OutJpg 2>$null
  Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
  return (Test-Path -LiteralPath $OutJpg)
}

# ── 创作者归类：拿 Stash 里的 Performer 名+别名做子串匹配 ────────
function RM-LoadCreators {
  try{
    $r=Invoke-RestMethod -Uri $Global:RM.Stash -Method Post -ContentType 'application/json' -Body '{"query":"{allPerformers{name alias_list}}"}'
    $list=@()
    foreach($p in $r.data.allPerformers){
      $list += [pscustomobject]@{ Name=$p.name; Keys=@(@($p.name)+@($p.alias_list) | Where-Object { $_ -and $_.Length -ge 2 }) }
    }
    return $list
  }catch{ RM-Log "警告: 取不到 Stash Performer 列表，归类将全部落到「待识别」"; return @() }
}

function RM-Classify { param([string]$Name,$Creators)
  foreach($c in $Creators){
    foreach($k in $c.Keys){ if($Name -like "*$k*"){ return $c.Name } }
  }
  return $null
}
