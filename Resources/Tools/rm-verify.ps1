# 对指定场景ID做密集抽帧，用于人工/视觉判定具体行为
param([Parameter(Mandatory=$true)][int[]]$Ids,[string]$Label='verify',[int]$N=9,[double]$From=0.15,[double]$To=0.92)
$u='http://127.0.0.1:9999/graphql'
$ff='C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe'
$fp='C:\Users\longm\AppData\Local\Stash\ffmpeg-btbn\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe'
$root='C:\Users\longm\AppData\Local\Temp\claude\R--\3e554192-78ac-44e7-a981-4f126375c782\scratchpad\frames'
$W=620;$H=440
$VF="scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:white,format=yuvj420p"

foreach($id in $Ids){
  $q=@{query='query($i:[ID!]){findScenes(scene_filter:{id:{value:0,modifier:NOT_NULL}},ids:$i){scenes{id files{path duration}}}}';variables=@{i=@("$id")}}|ConvertTo-Json -Depth 8 -Compress
  $s=(Invoke-RestMethod -Uri $u -Method Post -ContentType 'application/json' -Body $q).data.findScenes.scenes[0]
  if(-not $s){ "场景 $id 未找到"; continue }
  $path=$s.files[0].path; $d=[double]$s.files[0].duration
  if($d -le 2){ [double]::TryParse((& $fp -v error -show_entries format=duration -of csv=p=0 $path 2>$null),[ref]$d)|Out-Null }
  $seq=Join-Path $root ("v_${Label}_$id"); New-Item -ItemType Directory -Force -Path $seq|Out-Null
  for($k=0;$k -lt $N;$k++){
    $ts=[math]::Round($d*($From+($To-$From)*$k/[math]::Max(1,$N-1)),2)
    $o=Join-Path $seq ("{0:d2}.jpg" -f ($k+1))
    & $ff -v error -y -ss $ts -i $path -frames:v 1 -vf $VF -q:v 2 $o 2>$null
    if(-not(Test-Path -LiteralPath $o)){ & $ff -v error -y -f lavfi -i "color=c=gray:s=${W}x${H}" -frames:v 1 -vf "format=yuvj420p" -q:v 2 $o 2>$null }
  }
  $cols=3; $rows=[math]::Ceiling($N/$cols)
  & $ff -v error -y -framerate 1 -i (Join-Path $seq '%02d.jpg') -vf "tile=${cols}x${rows}:margin=5:padding=5:color=white" -frames:v 1 -q:v 2 (Join-Path $root "V-$Label-$id.jpg") 2>$null
  "[$id] " + ($path -replace '^R:\\Media\\创作者\\','')
}
