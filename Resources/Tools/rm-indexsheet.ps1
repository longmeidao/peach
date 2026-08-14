# 每个文件抽1帧，25个一张索引图，用于逐文件判定水印归属
param(
  [Parameter(Mandatory=$true)][string]$Dir,
  [Parameter(Mandatory=$true)][string]$Label,
  [string]$Exclude = '',
  [string]$Include = ''
)
$ff='C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe'
$fp='C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe'
$root='C:\Users\longm\AppData\Local\Temp\claude\R--\3e554192-78ac-44e7-a981-4f126375c782\scratchpad\frames'
$vid='.mp4','.mkv','.mov','.avi','.m4v','.wmv','.flv','.webm','.ts'
$W=520;$H=380
$VF="scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:white,format=yuvj420p"

$all=@(Get-ChildItem -LiteralPath $Dir -Recurse -File | Where-Object { $vid -contains $_.Extension.ToLower() })
if($Include){ $all=@($all | Where-Object { $_.Name -like "*$Include*" }) }
if($Exclude){ foreach($e in ($Exclude -split ',')){ $all=@($all | Where-Object { $_.Name -notlike "*$e*" }) } }
$all=@($all | Sort-Object Name)
"总文件: $($all.Count)"

$idx=@()
$page=0; $inPage=0
$seq=$null
for($i=0; $i -lt $all.Count; $i++){
  if($inPage -eq 0){
    $page++
    $seq=Join-Path $root ("p_${Label}_$page"); New-Item -ItemType Directory -Force -Path $seq|Out-Null
  }
  $inPage++
  $f=$all[$i]
  $d=0.0; [double]::TryParse((& $fp -v error -show_entries format=duration -of csv=p=0 $f.FullName 2>$null),[ref]$d)|Out-Null
  if($d -le 2){$d=20}
  $o=Join-Path $seq ("{0:d3}.jpg" -f $inPage)
  & $ff -v error -y -ss ([math]::Round($d*0.5,2)) -i $f.FullName -frames:v 1 -vf $VF -q:v 2 $o 2>$null
  if(-not(Test-Path -LiteralPath $o)){ & $ff -v error -y -f lavfi -i "color=c=gray:s=${W}x${H}" -frames:v 1 -vf "format=yuvj420p" -q:v 2 $o 2>$null }
  $idx += [pscustomobject]@{ 页=$page; 格=$inPage; 文件名=$f.Name; 路径=$f.FullName }
  if($inPage -eq 25 -or $i -eq $all.Count-1){
    while($inPage -lt 25){ $inPage++; & $ff -v error -y -f lavfi -i "color=c=white:s=${W}x${H}" -frames:v 1 -vf "format=yuvj420p" -q:v 2 (Join-Path $seq ("{0:d3}.jpg" -f $inPage)) 2>$null }
    & $ff -v error -y -framerate 1 -i (Join-Path $seq '%03d.jpg') -vf "tile=5x5:margin=4:padding=4:color=white" -frames:v 1 -q:v 2 (Join-Path $root ("P-${Label}-$page.jpg")) 2>$null
    "  页$page 完成"
    $inPage=0
  }
}
$idx | Export-Csv -LiteralPath (Join-Path $root "idx-$Label.csv") -NoTypeInformation -Encoding UTF8
"索引: $(Join-Path $root "idx-$Label.csv")  共 $page 页"
