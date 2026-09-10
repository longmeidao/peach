import { afterEach, beforeEach, expect, it, vi } from 'vitest';
// @ts-expect-error 浏览器共享控件使用正式实现。
import { wireLoadMore, wireHorizontalScroller, sortControlsHtml, filterChipHtml } from '../../web/js/ui-components.js';

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

it('横向滚动在边缘交还滚轮，重复绑定与移除都释放资源', async () => {
  const node=button();let left=0;const disconnect=vi.fn();
  vi.stubGlobal('ResizeObserver',class {observe(){}disconnect=disconnect});
  Object.defineProperties(node,{clientWidth:{value:100},scrollWidth:{value:200},scrollLeft:{get:()=>left,set:value=>{left=Math.max(0,Math.min(100,value))}}});
  const control=wireHorizontalScroller(node,{drag:true});
  expect(wireHorizontalScroller(node)).toBe(control);
  const wheel=()=>new WheelEvent('wheel',{deltaY:100,cancelable:true});
  const moving=wheel();node.dispatchEvent(moving);node.dispatchEvent(new Event('scroll'));
  expect(moving.defaultPrevented).toBe(true);expect(node.dataset.overflowRight).toBe('false');
  const edge=wheel();node.dispatchEvent(edge);expect(edge.defaultPrevented).toBe(false);
  node.remove();await vi.waitFor(()=>expect(disconnect).toHaveBeenCalledOnce());
  left=0;node.dispatchEvent(wheel());expect(left).toBe(0);
});

it('排序空选项可用，标签内容与属性均转义', () => {
  expect(sortControlsHtml()).toContain('aria-label="换一批"');
  const node=document.createElement('div');node.innerHTML=filterChipHtml('<script>',{attr:'data-tag',value:'"<',selected:true,count:0});
  expect(node.querySelector('script')).toBeNull();expect(node.querySelector('button')?.dataset.tag).toBe('"<');
  expect(node.textContent).toBe('<script> 0');
});
