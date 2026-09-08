import { beforeEach, expect, it } from 'vitest';
import { sidebarSectionHtml, wireSidebarGroups } from '../src/sidebar-groups';
beforeEach(()=>{document.body.replaceChildren();sessionStorage.clear()});
it('opens selected filters and preserves the user disclosure choice after rendering',()=>{
  const render=()=>{document.body.innerHTML=sidebarSectionHtml('标签','<button aria-pressed="true">已选标签</button>');wireSidebarGroups(document.body)};
  render();expect(document.querySelector<HTMLElement>('.board-sidebar-body')!.hidden).toBe(false);
  document.querySelector<HTMLButtonElement>('.board-section-toggle')!.click();
  render();expect(document.querySelector<HTMLElement>('.board-sidebar-body')!.hidden).toBe(true);
  expect(document.querySelector('.board-section-toggle')!.getAttribute('aria-expanded')).toBe('false');
});
it('escapes titles and retains a valid disclosure target',()=>{
  document.body.innerHTML=sidebarSectionHtml('<img>', '<button>条目</button>');wireSidebarGroups(document.body);
  expect(document.querySelector('img')).toBeNull();
  const button=document.querySelector('.board-section-toggle')!;
  expect(document.getElementById(button.getAttribute('aria-controls')!)).not.toBeNull();
});
