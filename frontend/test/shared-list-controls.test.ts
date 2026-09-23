import { afterEach, beforeEach, expect, it, vi } from 'vitest';
// @ts-expect-error 浏览器共享控件使用正式实现。
import { wireLoadMore, wireHorizontalScroller, rubberBand, sortControlsHtml, filterChipHtml } from '../../web/js/ui-components.js';

let intersections: (() => void)[], disconnects: ReturnType<typeof vi.fn>[];
beforeEach(() => {
  intersections=[];disconnects=[];
  vi.stubGlobal('IntersectionObserver',class {
    disconnect=vi.fn();
    constructor(callback: (entries: {isIntersecting:boolean}[])=>void){intersections.push(()=>callback([{isIntersecting:true}]));disconnects.push(this.disconnect)}
    observe(){}
  });
});
afterEach(async () => {document.body.replaceChildren();await new Promise(resolve=>setTimeout(resolve,0));vi.unstubAllGlobals()});
function button(){const node=document.createElement('button');document.body.append(node);return node}

it('点击与观察器共享请求锁，重接消费者仍只追加一次', async () => {
  const node=button(),apply=vi.fn();let done!:(value:number)=>void;
  const read=vi.fn(()=>new Promise<number>(resolve=>{done=resolve}));
  const control=wireLoadMore(node,{read,apply});
  const pending=control.run();node.click();intersections[0]!();
  expect(wireLoadMore(node,{read,apply})).toBe(control);
  expect(read).toHaveBeenCalledOnce();expect(node.getAttribute('aria-busy')).toBe('true');expect(node.disabled).toBe(false);
  done(2);await pending;
  expect(apply).toHaveBeenCalledExactlyOnceWith(2);expect(node.hasAttribute('aria-busy')).toBe(false);
});

it('失败保留原位重试，观察器不会自动重复失败请求', async () => {
  const node=button(),apply=vi.fn();
  const read=vi.fn().mockRejectedValueOnce(new Error('网络暂不可用')).mockResolvedValueOnce(3);
  const control=wireLoadMore(node,{read,apply});await control.run();
  expect(document.querySelector('[role="alert"]')).not.toBeNull();
  intersections[0]!();await control.run();expect(read).toHaveBeenCalledOnce();
  document.querySelector<HTMLButtonElement>('[data-note-action]')!.click();
  await vi.waitFor(()=>expect(apply).toHaveBeenCalledExactlyOnceWith(3));
  expect(document.querySelector('[role="alert"]')).toBeNull();
});

it('导航代际变化或卸载后不接受在途结果，卸载断开观察器', async () => {
  const node=button(),apply=vi.fn();let current=true,done!:(value:number)=>void,signal!:AbortSignal;
  const read=(next:AbortSignal)=>{signal=next;return new Promise<number>(resolve=>{done=resolve})};
  const control=wireLoadMore(node,{read,apply,isCurrent:()=>current});
  const first=control.run();current=false;done(1);await first;expect(apply).not.toHaveBeenCalled();
  current=true;const next=control.run();node.remove();
  await vi.waitFor(()=>expect(signal.aborted).toBe(true));done(2);await next;
  expect(disconnects[0]).toHaveBeenCalledOnce();expect(apply).not.toHaveBeenCalled();
});

it('在横排上开头的滚轮手势整段归这一排，鼠标一格逐帧走完、半路接着加，拦不住的留给页面，重复绑定与移除都释放资源', async () => {
  const node=button();let left=0,now=1000;const disconnect=vi.fn();
  vi.stubGlobal('ResizeObserver',class {observe(){}disconnect=disconnect});
  const frames:FrameRequestCallback[]=[];
  vi.stubGlobal('requestAnimationFrame',(callback:FrameRequestCallback)=>frames.push(callback));
  vi.stubGlobal('cancelAnimationFrame',()=>{frames.length=0});
  const step=()=>{now+=16;frames.shift()!(now)};
  const flush=()=>{for(let i=0;i<200&&frames.length;i+=1)step()};
  const clock=vi.spyOn(performance,'now').mockImplementation(()=>now);
  const clamp=(value:number)=>Math.max(0,Math.min(100,value));
  Object.defineProperties(node,{clientWidth:{value:100},scrollWidth:{value:200},scrollLeft:{get:()=>left,set:value=>{left=clamp(value)}}});
  node.animate=(()=>({cancel(){},onfinish:null})) as never;
  const control=wireHorizontalScroller(node,{drag:true});
  expect(wireHorizontalScroller(node)).toBe(control);
  const wheel=(deltaY=100,cancelable=true)=>new WheelEvent('wheel',{deltaY,cancelable});
  // 鼠标一格逐帧走，不是一下跳过去。
  const moving=wheel(60);node.dispatchEvent(moving);
  expect(moving.defaultPrevented).toBe(true);expect(left).toBe(0);
  step();expect(left).toBeGreaterThan(0);expect(left).toBeLessThan(60);
  // 半路再来一格，从上一格的终点接着算，一路走到头停下。
  now+=40;node.dispatchEvent(wheel(60));flush();
  expect(left).toBe(100);expect(frames).toHaveLength(0);
  node.dispatchEvent(new Event('scroll'));expect(node.dataset.overflowRight).toBe('false');
  // 到头以后还在转、隔一会再转，都不交给页面：要滚整页得把指针挪出这一排。
  now+=40;const still=wheel(60);node.dispatchEvent(still);expect(still.defaultPrevented).toBe(true);
  now+=1000;const next=wheel(60);node.dispatchEvent(next);expect(next.defaultPrevented).toBe(true);
  expect(left).toBe(100);
  // 触控板的小步直接跟手，不套动画。
  left=50;now+=1000;node.dispatchEvent(wheel(-10));
  expect(left).toBe(40);expect(frames).toHaveLength(0);
  // 页面那边开了头的手势拦不住，这一排也不跟着动。
  left=0;now+=1000;node.dispatchEvent(wheel(100,false));expect(left).toBe(0);
  clock.mockRestore();
  node.remove();await vi.waitFor(()=>expect(disconnect).toHaveBeenCalledOnce());
  left=0;node.dispatchEvent(wheel());expect(left).toBe(0);
});

it('横排推过头按橡皮筋收敛，顶在边上再推也弹，一次滚轮手势只弹一下，拖过头松手弹回', () => {
  expect(rubberBand(0,400)).toBe(0);
  expect(rubberBand(100,400)).toBeGreaterThan(0);expect(rubberBand(100,400)).toBeLessThan(100);
  expect(rubberBand(-100,400)).toBe(-rubberBand(100,400));
  expect(rubberBand(1e6,400)).toBeLessThan(400);
  const node=button();let left=100,now=1000;
  vi.stubGlobal('ResizeObserver',class {observe(){}disconnect(){}});
  vi.stubGlobal('matchMedia',()=>({matches:false}));
  const clock=vi.spyOn(performance,'now').mockImplementation(()=>now);
  Object.defineProperties(node,{clientWidth:{value:100},scrollWidth:{value:200},
    scrollLeft:{get:()=>left,set:value=>{left=Math.max(0,Math.min(100,value))}}});
  const animate=vi.fn(()=>({cancel(){},onfinish:null}));node.animate=animate as never;
  wireHorizontalScroller(node,{drag:true});
  const wheel=(deltaY:number)=>new WheelEvent('wheel',{deltaY,cancelable:true});
  // 顶在最右还往前推：这一格也归这一排，弹一下，往左。
  const push=wheel(30);node.dispatchEvent(push);
  expect(push.defaultPrevented).toBe(true);expect(animate).toHaveBeenCalledOnce();
  const [frames]=animate.mock.calls[0] as unknown as [Record<string,string>[]];
  expect(parseFloat(frames[1]!['--edge-pull']!)).toBeLessThan(0);
  // 惯性尾巴接着撞边，同一次手势不再弹。
  now+=40;node.dispatchEvent(wheel(20));now+=40;node.dispatchEvent(wheel(10));
  expect(animate).toHaveBeenCalledOnce();
  // 下一次手势从半路滚过头，再弹一次。
  left=90;now+=1000;node.dispatchEvent(wheel(30));
  expect(left).toBe(100);expect(animate).toHaveBeenCalledTimes(2);
  // 拖过左端：内容跟手右移、比手少走；松手从那里弹回原位。
  // happy-dom 的 `pageX` 恒为 0，照浏览器的样子补上。
  const mouse=(type:string,pageX=0)=>Object.defineProperty(new MouseEvent(type,{button:0}),'pageX',{value:pageX});
  left=0;node.dispatchEvent(mouse('mousedown'));
  window.dispatchEvent(mouse('mousemove',80));
  const pulled=parseFloat(node.style.getPropertyValue('--edge-pull'));
  expect(pulled).toBeGreaterThan(0);expect(pulled).toBeLessThan(80);
  expect(node.classList.contains('edgepull')).toBe(true);
  window.dispatchEvent(new MouseEvent('mouseup'));
  expect(node.style.getPropertyValue('--edge-pull')).toBe('');
  expect(animate).toHaveBeenCalledTimes(3);
  clock.mockRestore();
});

it('排序空选项可用，标签内容与属性均转义', () => {
  expect(sortControlsHtml()).toContain('aria-label="换一批"');
  const node=document.createElement('div');node.innerHTML=filterChipHtml('<script>',{attr:'data-tag',value:'"<',selected:true,count:0});
  expect(node.querySelector('script')).toBeNull();expect(node.querySelector('button')?.dataset.tag).toBe('"<');
  // 计数前不写空格：`.pill` 是 flex 容器，纯空白文本节点不参与布局，间隔归 `.pill .n` 的外边距。
  expect(node.textContent).toBe('<script>0');
});
