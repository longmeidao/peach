import { afterEach, expect, it, vi } from 'vitest';
// @ts-expect-error 遗留模块由浏览器直接加载。
import { mountFilterFrame } from '../../web/js/ui-components.js';

afterEach(() => document.body.replaceChildren());

it('切换列表只替换读数与控件，保留浮层和筛选事件', () => {
  document.body.innerHTML='<header><button>全部</button><nav>标签</nav></header><main><footer><h3>视频</h3><aside>排序</aside></footer></main>';
  const top=document.querySelector('header')!;
  const views=top.querySelector('button')!;
  const change=vi.fn(); views.addEventListener('click',change);
  const slots={views,tags:top.querySelector('nav'),readout:document.querySelector('h3'),controls:document.querySelector('aside')};
  const frame=mountFilterFrame(top,document.querySelector('footer'),slots);
  const main=document.querySelector('main')!;
  main.innerHTML='<footer><h3>照片</h3><aside>大小</aside></footer><article>照片内容</article>';
  const next=mountFilterFrame(top,main.querySelector('footer'),{...slots,readout:main.querySelector('h3'),controls:main.querySelector('aside')});
  expect(next).toBe(frame);
  expect(frame.querySelectorAll('[data-filter-row="bottom"]')).toHaveLength(1);
  expect([...frame.querySelectorAll('[data-filter-slot]')].map(node=>node.getAttribute('data-filter-slot'))).toEqual(['views','tags','readout','controls']);
  expect(main.textContent).toBe('照片内容');
  expect(frame.textContent).toContain('照片');
  views.click();expect(change).toHaveBeenCalledOnce();
  mountFilterFrame(top,frame.querySelector('footer'),{...slots,readout:frame.querySelector('h3'),controls:frame.querySelector('aside')});
  expect(document.querySelectorAll('[data-filter-frame]')).toHaveLength(1);
});

it('集合工具条更新后键盘焦点停留在同一排序操作', () => {
  document.body.innerHTML='<header></header><footer><button data-sort="name">名称</button></footer>';
  const top=document.querySelector('header')!,bottom=document.querySelector('footer')!;
  const frame=mountFilterFrame(top,bottom,{});bottom.querySelector('button')!.focus();
  const next=document.createElement('footer');next.innerHTML='<button data-sort="new">最新</button><button data-sort="name">名称</button>';
  mountFilterFrame(top,next,{});
  expect(document.activeElement).toBe(frame.querySelector('[data-sort="name"]'));
});
