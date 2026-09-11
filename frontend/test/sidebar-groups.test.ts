import { beforeEach, expect, it, vi } from 'vitest';
vi.mock('@peach/legacy/ui',()=>vi.importActual('../../web/js/ui-components.js'));
import { sidebarSectionHtml, wireSidebarGroups, transitionTheme } from '../src/sidebar-groups';
beforeEach(()=>{document.body.replaceChildren();sessionStorage.clear()});
it('theme snapshots restore live glass after completion or rejection and apply once',async()=>{
  vi.stubGlobal('matchMedia',()=>({matches:false}));
  const button=document.createElement('button');document.body.append(button);
  for(const rejects of [false,true]){
    const apply=vi.fn();
    let finish!:()=>void;
    const finished=new Promise<void>((resolve,reject)=>{finish=()=>rejects?reject(new Error('skip')):resolve()});
    const start=vi.fn((update:()=>void)=>{
      expect(document.documentElement.dataset.themeSnapshot).toBe('true');
      update();return{finished};
    });
    Object.defineProperty(document,'startViewTransition',{configurable:true,value:start});
    const pending=transitionTheme(button,apply);
    expect(apply).toHaveBeenCalledTimes(1);
    finish();await pending;
    expect(apply).toHaveBeenCalledTimes(1);
    expect(document.documentElement.hasAttribute('data-theme-snapshot')).toBe(false);
    expect([...document.head.querySelectorAll('style')].some(style=>style.textContent?.includes('peach-theme-reveal'))).toBe(false);
  }
  Reflect.deleteProperty(document,'startViewTransition');vi.unstubAllGlobals();
});
it('opens selected filters and preserves the user disclosure choice after rendering',()=>{
  const render=()=>{document.body.innerHTML=sidebarSectionHtml('标签','<button aria-pressed="true">已选标签</button>');wireSidebarGroups(document.body)};
  render();expect(document.querySelector<HTMLDetailsElement>('[data-sidebar-group]')!.open).toBe(true);
  document.querySelector<HTMLButtonElement>('.board-section-toggle')!.click();
  render();expect(document.querySelector<HTMLDetailsElement>('[data-sidebar-group]')!.open).toBe(false);
  expect(document.querySelector('.board-section-toggle')!.getAttribute('aria-expanded')).toBe('false');
});
it('puts the load more control at the end of the list it belongs to',()=>{
  document.body.innerHTML=sidebarSectionHtml('创作者','<div class="chips"><button>条目</button></div>',
    '<button class="sidemore">更多</button>');
  wireSidebarGroups(document.body);
  expect(document.querySelector('summary .sidemore')).toBeNull();
  const body=document.querySelector('.board-sidebar-body')!;
  expect(body.lastElementChild!.className).toBe('sidemore');
  // 收起这一组时它跟名单一起收走：名单都不在了，「还没完」也就无从说起。
  expect(document.querySelector<HTMLDetailsElement>('[data-sidebar-group]')!.open).toBe(false);
});
it('escapes titles and retains a valid disclosure target',()=>{
  document.body.innerHTML=sidebarSectionHtml('<img>', '<button>条目</button>');wireSidebarGroups(document.body);
  expect(document.querySelector('img')).toBeNull();
  const button=document.querySelector('.board-section-toggle')!;
  expect(document.getElementById(button.getAttribute('aria-controls')!)).not.toBeNull();
});
