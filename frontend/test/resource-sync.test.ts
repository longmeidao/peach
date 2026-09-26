import { describe, expect, it } from 'vitest';
import { resourceScanHtml, type ResourceSource } from '../src/resource-sync';

const source = (location: string, online = true): ResourceSource => ({
  location, online, total: 20, missing: online ? 2 : 0, empty: online ? 3 : 0, unreadable: online ? 2 : 0});
describe('文件检查结果', () => {
  it.each([['local'], ['115', 'pikpak'], ['local', '115', 'pikpak']])('呈现实际来源 %s', (...locations) => {
    document.body.innerHTML = resourceScanHtml({sources: locations.map(location => source(location)), missing: 2, empty: 3}, () => '0 B');
    const [sources, totals] = document.querySelectorAll('.resourcestats');
    expect(sources!.querySelectorAll('.board-plain-stat')).toHaveLength(locations.length);
    expect([...totals!.querySelectorAll('.board-plain-stat-head')].map(head => head.textContent))
      .toEqual(['待永久删除', '空文件夹', '可清理的缓存']);
    expect(document.body.textContent).toContain('找不到文件 · 共 20 项');
    expect(document.body.textContent).toContain('空文件夹 3 个');
    expect(document.body.textContent).toContain('2 个目录读取失败，已跳过');
    expect(document.querySelector('.geist-note')?.textContent).toContain('这一步不可撤销');
    const apply = document.querySelector('#resourceApply');
    expect(apply?.textContent).toBe('清理失效条目');
    expect(apply?.className).toBe('danger');
  });
  it('离线来源没有删除判断，零差异没有清理按钮', () => {
    document.body.innerHTML = resourceScanHtml({sources: [source('local', false)]}, () => '0 B');
    expect(document.body.textContent).toContain('离线，已跳过');
    expect(document.body.textContent).toContain('馆藏中有 20 项');
    expect(document.querySelector('strong')?.textContent).toBe('—');
    expect(document.querySelector('#resourceApply')).toBeNull();
  });
  it('只有空文件夹或只有缓存待清理也提供清理入口', () => {
    document.body.innerHTML = resourceScanHtml({empty: 4}, () => '0 B');
    expect(document.querySelector('#resourceApply')).not.toBeNull();
    document.body.innerHTML = resourceScanHtml({cache: {files: 643, bytes: 48 * 1024 ** 2}}, () => '48 MiB');
    expect(document.body.textContent).toContain('643 个');
    expect(document.body.textContent).toContain('48 MiB');
    expect(document.querySelector('#resourceApply')).not.toBeNull();
  });
});
