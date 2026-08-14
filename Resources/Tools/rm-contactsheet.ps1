# 批量生成关键帧接触表（读取水印/账号识别创作者）
# 关键：抽帧时即统一画布尺寸，否则 image2 在分辨率变化处会中断
param([Parameter(Mandatory=$true)][string[]]$Targets)

$ff  = 'C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe'
$fp  = 'C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe'
$root= 'C:\Users\longm\AppData\Local\Temp\claude\R--\3e554192-78ac-44e7-a981-4f126375c782\scratchpad\frames'
$vid = '.mp4','.mkv','.mov','.avi','.m4v','.wmv','.flv','.webm','.ts','.mpg','.mpeg'
$NV = 4; $NF = 4
$W = 560; $H = 400
$VF = "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:white,format=yuvj420p"

foreach ($t in $Targets) {
  $parts = $t -split '\|'
  $label = $parts[0]; $dir = $parts[1]
  if (-not (Test-Path -LiteralPath $dir)) { Write-Output "MISSING: $label"; continue }

  $seq = Join-Path $root ("q_" + $label)
  New-Item -ItemType Directory -Force -Path $seq | Out-Null

  $all = @(Get-ChildItem -LiteralPath $dir -Recurse -File | Where-Object { $vid -contains $_.Extension.ToLower() -and $_.Length -gt 1MB } | Sort-Object FullName)
  if ($all.Count -eq 0) { Write-Output "NOVIDEO: $label"; continue }
  $step = [math]::Max(1, [math]::Floor($all.Count / $NV))
  $pick = @(); for ($j = 0; $j -lt $NV -and ($j*$step) -lt $all.Count; $j++) { $pick += $all[$j*$step] }

  $n = 0
  foreach ($f in $pick) {
    $dur = & $fp -v error -show_entries format=duration -of csv=p=0 $f.FullName 2>$null
    $d = 0.0; [double]::TryParse("$dur", [ref]$d) | Out-Null
    if ($d -le 2) { $d = 20 }
    for ($k = 1; $k -le $NF; $k++) {
      $n++
      $ts = [math]::Round($d * $k / ($NF + 1), 2)
      $o  = Join-Path $seq ("{0:d3}.jpg" -f $n)
      & $ff -v error -y -ss $ts -i $f.FullName -frames:v 1 -vf $VF -q:v 2 $o 2>$null
      if (-not (Test-Path -LiteralPath $o)) {
        & $ff -v error -y -f lavfi -i "color=c=gray:s=${W}x${H}" -frames:v 1 -vf "format=yuvj420p" -q:v 2 $o 2>$null
      }
    }
    Write-Output ("  [{0}] {1}" -f $label, $f.Name)
  }
  while ($n -lt ($NV*$NF)) {
    $n++
    $o = Join-Path $seq ("{0:d3}.jpg" -f $n)
    & $ff -v error -y -f lavfi -i "color=c=white:s=${W}x${H}" -frames:v 1 -vf "format=yuvj420p" -q:v 2 $o 2>$null
  }

  $sheet = Join-Path $root ("S2-" + $label + ".jpg")
  & $ff -v error -y -framerate 1 -i (Join-Path $seq '%03d.jpg') -vf "tile=${NF}x${NV}:margin=6:padding=6:color=white" -frames:v 1 -q:v 2 $sheet 2>$null
  if (Test-Path -LiteralPath $sheet) { Write-Output "OK $label" } else { Write-Output "FAIL $label" }
}
