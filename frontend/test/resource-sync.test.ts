import { describe, expect, it } from 'vitest';
import { resourceScanHtml, type ResourceSource } from '../src/resource-sync';

const source = (location: string, online = true): ResourceSource => ({location, online, checked: 18, total: 20, missing: online ? 2 : 0, unreadable: online ? 2 : 0});
describe('文件检查结果', () => {
  it.each([['local'], ['115', 'pikpak'], ['local', '115', 'pikpak']])('呈现实际来源 %s', (...locations) => {
    document.body.innerHTML = resourceScanHtml({sources: locations.map(location => source(location)), missing: 2}, () => '0 B');
    expect(document.querySelectorAll('.resourcesources article')).toHaveLength(locations.length);
    expect(document.body.textContent).toContain('找不到文件');
    expect(document.body.textContent).toContain('2 项读取失败，已跳过');
    expect(document.querySelector('#resourceApply')?.textContent).toBe('清理失效记录与缓存');
  });
  it('离线来源没有删除判断，零差异没有清理按钮', () => {
    document.body.innerHTML = resourceScanHtml({sources: [source('local', false)]}, () => '0 B');
    expect(document.body.textContent).toContain('离线，已跳过');
    expect(document.body.textContent).not.toContain('已从网盘删除');
    expect(document.querySelector('strong')?.textContent).toBe('—');
    expect(document.querySelector('#resourceApply')).toBeNull();
  });
  it('仅缓存待清理也提供清理入口', () => {
    document.body.innerHTML = resourceScanHtml({cache: {files: 643, bytes: 48 * 1024 ** 2}}, () => '48 MiB');
    expect(document.body.textContent).toContain('643 个');
    expect(document.body.textContent).toContain('48 MiB');
    expect(document.querySelector('#resourceApply')).not.toBeNull();
  });
});
