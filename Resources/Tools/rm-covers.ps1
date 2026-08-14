param([switch]$Execute)
$u='http://127.0.0.1:9999/graphql'
$ff='C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe'
$out='C:\Users\longm\AppData\Local\Temp\claude\R--\3e554192-78ac-44e7-a981-4f126375c782\scratchpad\covers'
New-Item -ItemType Directory -Force -Path $out | Out-Null
function GQ($q,$v){ $b=@{query=$q}; if($v){$b.variables=$v}
  $r=Invoke-RestMethod -Uri $u -Method Post -ContentType 'application/json' -Body ($b|ConvertTo-Json -Depth 12 -Compress)
  if($r.errors){ throw ($r.errors|ConvertTo-Json -Depth 6) }; $r.data }

$perfs=(GQ '{allPerformers{id name scene_count image_path}}').allPerformers | Where-Object {[int]$_.scene_count -gt 0}
"有场景的 Performer: $($perfs.Count)"

foreach($p in $perfs){
  $q=@{query='query($t:[ID!]){findScenes(scene_filter:{performers:{value:$t,modifier:INCLUDES}},filter:{per_page:-1}){scenes{id files{path width height duration}}}}';variables=@{t=@($p.id)}}|ConvertTo-Json -Depth 8 -Compress
  $sc=(Invoke-RestMethod -Uri $u -Method Post -ContentType 'application/json' -Body $q).data.findScenes.scenes
  if(-not $sc){ continue }
  # 选分辨率最高、时长>30s 的片子
  $best=$sc | Where-Object { [double]$_.files[0].duration -gt 30 } |
        Sort-Object @{e={[int]$_.files[0].width * [int]$_.files[0].height}} -Descending | Select-Object -First 1
  if(-not $best){ $best=$sc | Sort-Object @{e={[int]$_.files[0].width*[int]$_.files[0].height}} -Descending | Select-Object -First 1 }
  $path=$best.files[0].path; $d=[double]$best.files[0].duration
  if($d -le 0){ $d=60 }

  # 5 个候选帧，取 JPEG 体积最大者（信息量最高，可避开纯黑/纯色/模糊帧）
  $cands=@()
  foreach($frac in 0.20,0.35,0.50,0.65,0.80){
    $f=Join-Path $out ("c_{0}_{1}.jpg" -f $p.id,[int]($frac*100))
    & $ff -v error -y -ss ([math]::Round($d*$frac,2)) -i $path -frames:v 1 -vf "scale=720:-2" -q:v 2 $f 2>$null
    if(Test-Path -LiteralPath $f){ $cands+=(Get-Item -LiteralPath $f) }
  }
  if($cands.Count -eq 0){ "  跳过(抽帧失败): $($p.name)"; continue }
  $pick=$cands | Sort-Object Length -Descending | Select-Object -First 1
  $final=Join-Path $out ("cover_{0}.jpg" -f $p.id)
  Copy-Item -LiteralPath $pick.FullName -Destination $final -Force
  "  {0,-22} <- {1}  ({2}KB)" -f $p.name,(Split-Path $path -Leaf),[int]($pick.Length/1KB)

  if($Execute){
    $b64=[Convert]::ToBase64String([IO.File]::ReadAllBytes($final))
    GQ 'mutation($id:ID!,$img:String!){performerUpdate(input:{id:$id,image:$img}){id}}' @{id=$p.id;img="data:image/jpeg;base64,$b64"} | Out-Null
  }
}
if(-not $Execute){ "`n== 预览模式，未写入 Stash ==" } else { "`n== 封面已写入 Stash ==" }
