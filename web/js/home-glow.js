/* 侧栏光晕的纯数据层：参数模型、预设、命名色板、读回存量的规范化，以及把颜色写到
   指定元素上的那一次绘制。没有页面装配，也不认识 `appSettings`、`$`、`saveSettings`
   这些 app.js 的全局——侧栏那枚配色钮、它的弹层和设置面板的参数区仍旧留在 app.js。

   拆出来是为了迁移时只搬一次：React 壳直接 import 这一份，不用把同一张预设表、同一
   套色板和同一段规范化再抄进组件里。同一个道理，这里不从 `../dist/peach-ui.js` 借东西
   ——那是 React 的构建产物，它自己要 import 本文件，反向引用就闭成了一个环。
   `glowNumber` 与它的 `boundedPreference`（`frontend/src/number-setting.ts`）判据相同：
   整数且落在区间里才算数，否则退回默认那一档。

   `paintHomeGlow` 只写传进来的那枚元素。写在 <html> 上整棵树都要重算样式，实测每帧
   15ms 上下，拖拉条时帧预算当场就超；量法记在 web/css/01-base.css 那条规则上面。 */

/* 一档配色就是三枚光晕的颜色与不透明度；开关、强度和颗粒不属于配色，换档时不动。
   椭圆半轴和收边位置不在这里，只有 web/css/01-base.css 一份，用户不调、也不存；圆心
   根本不存在——三枚光晕由 glowdrift 那两条动画一直推着走，那是侧栏玻璃自带的漂移。
   这个形状借自 feralui.dev/gradients 的 JSON 导出（登记在 docs/HANDOFF.md），只借参数
   模型，渲染仍是那三层纯 CSS 径向渐变，不引入 Canvas。
   三枚光晕各自向 transparent 收边，落在侧栏那块玻璃上，所以每一枚都得自己亮得起来：
   压暗的那种颜色在深色侧栏上等于没有，在浅色侧栏上是一团脏。
   `amber` 是默认那一档，和 :root 上的默认值一字不差。 */
const HOME_GLOW_SPOTS=['spot1','spot2','spot3'];
const GLOW_SPOT_LABELS=['光晕一','光晕二','光晕三'];
const HOME_GLOW_PRESETS=[
  ['amber','钨丝暖阁',{
    spot1:{color:'#e08a2f',alpha:62},spot2:{color:'#c4544a',alpha:52},spot3:{color:'#a86a52',alpha:52}}],
  ['plum','夜樱',{
    spot1:{color:'#b455a0',alpha:64},spot2:{color:'#6a4fd0',alpha:54},spot3:{color:'#7a4f96',alpha:56}}],
  ['pine','深林',{
    spot1:{color:'#3f9e57',alpha:66},spot2:{color:'#7fae4a',alpha:48},spot3:{color:'#4f9463',alpha:56}}],
  ['ash','灰雾',{
    spot1:{color:'#8f98a4',alpha:52},spot2:{color:'#b6bcc4',alpha:38},spot3:{color:'#6f7783',alpha:50}}],
];
/* 手调过颜色之后当前档就不再是任何一个预设，侧栏那一格和面板顶上的标识要如实说这件事，
   不能继续顶着上一档的名字。 */
const HOME_GLOW_CHOICES=[...HOME_GLOW_PRESETS.map(([key,label])=>[key,label]),['custom','自定义']];
const glowPresetName=key=>(HOME_GLOW_CHOICES.find(([name])=>name===key)||HOME_GLOW_CHOICES[0])[1];
const glowPalette=key=>structuredClone((HOME_GLOW_PRESETS.find(([name])=>name===key)||HOME_GLOW_PRESETS[0])[2]);
/* 挑颜色的那张色板。七个色系各六档明度，名字按颜色本身取，不按它被用在哪儿——同一枚
   颜色换到另一枚光晕上还是同一个名字。十二枚预设色全部落在这张表里，所以从侧栏选完
   预设再打开颜色弹层，选中环指得出当前那一格；表里缺哪一枚，那一枚就永远是「没选中」。
   青绿整段不收：它在深色侧栏上发冷、在浅色侧栏上发脏，这块玻璃用不上。 */
const GLOW_SWATCH_FAMILIES=[['all','全部'],['gray','灰'],['red','红'],['yellow','黄'],
  ['green','绿'],['blue','蓝'],['purple','紫'],['brown','棕']];
const GLOW_SWATCHES=[
  ['gray','云灰','#d8dade'],['gray','雾灰','#b6bcc4'],['gray','石灰','#8f98a4'],
  ['gray','铁灰','#6f7783'],['gray','墨灰','#4a4e56'],['gray','深灰','#2e3138'],
  ['red','樱红','#f08a8a'],['red','珊瑚','#e26a62'],['red','砖红','#c4544a'],
  ['red','朱红','#b5322f'],['red','酒红','#8e2a2c'],['red','暗红','#6b2224'],
  ['yellow','麦黄','#f2d48a'],['yellow','琥珀','#e8b451'],['yellow','钨丝','#e08a2f'],
  ['yellow','金黄','#cf8a20'],['yellow','姜黄','#a9701c'],['yellow','栗黄','#7d5216'],
  ['green','嫩芽','#a9cf7e'],['green','叶绿','#7fae4a'],['green','草绿','#5da34f'],
  ['green','森绿','#3f9e57'],['green','苔绿','#4f9463'],['green','墨绿','#27563a'],
  ['blue','天蓝','#9fc2e8'],['blue','湖蓝','#6a9fd8'],['blue','靛蓝','#4478c0'],
  ['blue','宝蓝','#2f5ba3'],['blue','深蓝','#27467c'],['blue','夜蓝','#1c3358'],
  ['purple','丁香','#c3a7e0'],['purple','品红','#b455a0'],['purple','薰衣草','#a67fd2'],
  ['purple','葡萄','#6a4fd0'],['purple','茄紫','#7a4f96'],['purple','深紫','#432c6d'],
  ['brown','沙棕','#d6b492'],['brown','陶棕','#bd8f68'],['brown','赭棕','#a86a52'],
  ['brown','栗棕','#8c5340'],['brown','褐棕','#6d3f31'],['brown','深褐','#4e2d23'],
];
const glowNumber=(value,min,max,fallback)=>Number.isInteger(value)&&value>=min&&value<=max?value:fallback;
const glowColor=(value,fallback)=>/^#[0-9a-f]{6}$/i.test(String(value))?String(value).toLowerCase():fallback;
const glowRgba=(hex,alpha)=>`rgba(${[1,3,5].map(at=>parseInt(hex.slice(at,at+2),16)).join(',')},${(alpha/100).toFixed(2)})`;
const DEFAULT_HOME_GLOW={on:true,preset:'amber',strength:100,noise:0,...glowPalette('amber')};
/* 光晕参数整份来自 localStorage，形态和范围都不可信：颜色写成任意字符串会让那一层
   渐变整条失效，百分比越界会把光晕糊成一整片或者缩没。逐项夹回区间、认不出就退回
   默认那一档，而不是整份丢掉——一个坏掉的数不该把用户调好的其余几档一起清空。
   只有一种情形要连颜色一起换掉：存着的档名已经不在清单里。那说明这一档被清退了，
   留在旁边的三枚颜色正是被清退的那一版，按坏值逐项夹回去只会把它原样留在页面上。
   自定义不在此列——那三枚颜色是用户自己挑的，档名认得出来，照样留着。
   已经不存在的键不必单独清理：这里只按当前模型逐项取值，重建出来的对象里没有它们。
   旧版本那套横躺在首页顶部的圆心与半轴就是这么掉的——几何现在只由 CSS 给，存过的那份
   要是跟着夹回来，老用户看到的还是半截光。 */
function normalizeHomeGlow(raw){
  const stored=raw&&typeof raw==='object'?raw:{};
  const known=HOME_GLOW_CHOICES.some(([key])=>key===stored.preset);
  const preset=known?stored.preset:'amber';
  const seed=glowPalette(preset==='custom'?'amber':preset);
  const glow={on:stored.on!==false,preset,
    strength:glowNumber(+stored.strength,0,100,100),
    noise:glowNumber(+stored.noise,0,100,0)};
  for(const key of HOME_GLOW_SPOTS){
    const spot=known&&stored[key]&&typeof stored[key]==='object'?stored[key]:{},fallback=seed[key];
    glow[key]={color:glowColor(spot.color,fallback.color),
      alpha:glowNumber(+spot.alpha,0,100,fallback.alpha)};
  }
  return glow;
}
/* 预设圆球那一圈：几枚颜色就等分成几段。写成函数是因为自定义档的颜色数和预设一样多，
   却要在弹层里现算一遍。 */
const glowChipFill=colors=>`conic-gradient(from -90deg,${colors.map((color,index)=>
  `${color} ${(index*100/colors.length).toFixed(3)}% ${((index+1)*100/colors.length).toFixed(3)}%`).join(',')})`;
/* 只写值，光晕怎么画留在 web/css/01-base.css 一份。关掉时强度和颗粒一起归零，
   `.glowlayer::before` 的不透明度按那句乘法算成 0，不另设一个「关」的分支——否则
   「关着」和「强度 0」会是两条各自演化的路径。

   写之前先和上一次写进这枚元素的值比一遍。这里有五个变量（强度、颗粒、三枚颜色），
   拖强度那条拉条时变的只有一个；不比就是每一步把五个都重设一遍，中间那四次全是白写。
   记账按元素分开存，多个壳各画各的那一层时不会互相把对方的值判成「已经写过」。 */
const glowWritten=new WeakMap();
function paintHomeGlow(el,glow){
  if(!el)return;
  let written=glowWritten.get(el);
  if(!written){written=new Map();glowWritten.set(el,written)}
  const live=glow.on;
  const write=(name,value)=>{
    if(written.get(name)===value)return;
    written.set(name,value);el.style.setProperty(name,value);
  };
  write('--glow-strength',String(live?glow.strength/100:0));
  write('--glow-noise',String(live?glow.noise/100:0));
  HOME_GLOW_SPOTS.forEach((key,index)=>{
    const spot=glow[key];
    write(`--glow-spot-${index+1}-color`,glowRgba(spot.color,spot.alpha));
  });
}

export {DEFAULT_HOME_GLOW, GLOW_SPOT_LABELS, GLOW_SWATCHES, GLOW_SWATCH_FAMILIES,
  HOME_GLOW_CHOICES, HOME_GLOW_PRESETS, HOME_GLOW_SPOTS,
  glowChipFill, glowColor, glowPalette, glowPresetName, normalizeHomeGlow, paintHomeGlow};
