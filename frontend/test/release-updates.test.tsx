import { render } from 'preact';
import { afterEach, expect, it, vi } from 'vitest';
import { ReleaseUpdates } from '../src/islands/release-updates';

// @ts-expect-error 遗留组件使用正式实现验证图标与提示语义。
vi.mock('@peach/legacy/ui', () => import('../../web/js/ui-components.js'));
const host = document.createElement('div');
afterEach(() => { render(null, host); host.remove(); });
const initial = { current_version:'0.22.2',latest_version:'0.22.3',channel:'测试版',installation:'独立测试包',state:'available',message:'发现新测试版 0.22.3。',release_url:'https://example.com/releases' };

it('可用更新用持续信息提示且检查为最新后移除提示', () => {
  document.body.append(host);
  render(<ReleaseUpdates initial={initial} />, host);
  expect(host.querySelector('[role="status"] .geist-note-secondary')?.textContent).toContain('有可用更新');
  expect(host.querySelector('.geist-note svg')).not.toBeNull();
  expect(host.querySelector('.geist-note-warning,.geist-note-error')).toBeNull();
  expect(host.textContent).toContain('下载并安装');
  render(null, host);
  render(<ReleaseUpdates initial={{...initial,state:'current',message:'已是最新测试版。'}} />, host);
  expect(host.querySelector('.geist-note')).toBeNull();
  expect(host.textContent).not.toContain('下载并安装');
});
