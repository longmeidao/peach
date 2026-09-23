import { expect, it, vi } from 'vitest';
import * as legacyUi from '@peach/legacy/ui';

import { MediaRepair, type MediaRepairState, type RepairLibrary } from '../../src/react/settings/media-repair';
import { buttonNamed, choose, click, fetchMock, mount, sentBody, settle } from './render';

const idle: MediaRepairState = {
  status: 'idle', library: '', stage: '', checked: 0, total: 0, found: 0,
  repaired: 0, failed: 0, missing_tool: 0, skipped: 0, message: '',
};
const libraries: RepairLibrary[] = [
  { id: '网盘', name: '网盘', metered: false },
  { id: 'PikPak', name: 'PikPak', metered: true },
];

type Confirmation = Parameters<typeof legacyUi.confirmModal>[0];

/** 确认弹层直接点确认，并记下弹层上写的是什么。 */
function confirmEverything() {
  const seen: Confirmation[] = [];
  vi.spyOn(legacyUi, 'confirmModal').mockImplementation((async (options: Confirmation) => {
    seen.push(options);
    await options.onConfirm?.();
    return { confirmed: true };
  }) as typeof legacyUi.confirmModal);
  return seen;
}

it('开始修复先确认，确认后把选中的库发过去，随后按服务端的进度报扫描到哪一部', async () => {
  vi.useFakeTimers();
  const seen = confirmEverything();
  const fetcher = fetchMock(200, { ...idle, status: 'running', library: 'PikPak', stage: '扫描', checked: 3, total: 12 });
  vi.stubGlobal('fetch', fetcher);
  const host = await mount(<MediaRepair initial={idle} initialLibraries={libraries} />);
  await choose(host.querySelector('[aria-haspopup="listbox"]'), 'PikPak');
  await click(buttonNamed('开始修复', host));
  await settle();
  expect(seen[0]?.title).toBe('修复媒体库「PikPak」');
  expect(seen[0]?.confirmLabel).toBe('修复媒体库');
  expect(seen[0]?.body).toContain('每修一部都要把片子完整拉一遍');
  expect(fetcher.mock.calls[0]?.[0]).toBe('/api/media-repair');
  expect(sentBody(fetcher)).toEqual({ library: 'PikPak', restart: true });
  expect(host.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow')).toBe('25');
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('扫描 3 / 12');
  expect(buttonNamed('停止', host)).not.toBeNull();
});

it('不在计费来源上的库，确认正文不提流量', async () => {
  const seen = confirmEverything();
  vi.stubGlobal('fetch', fetchMock(200, idle));
  const host = await mount(<MediaRepair initial={idle} initialLibraries={libraries} />);
  await click(buttonNamed('开始修复', host));
  await settle();
  expect(seen[0]?.title).toBe('修复媒体库「网盘」');
  expect(seen[0]?.body).toContain('坏原件改名成同目录的隐藏文件');
  expect(seen[0]?.body).not.toContain('拉一遍');
});

it('修复阶段点名当前这部片，停止之后回到可以再开始的样子', async () => {
  vi.useFakeTimers();
  const fetcher = fetchMock(200, { ...idle, status: 'complete', library: '网盘', stage: '完成', repaired: 2 });
  vi.stubGlobal('fetch', fetcher);
  const host = await mount(<MediaRepair initialLibraries={libraries} initial={{
    ...idle, status: 'running', library: '网盘', stage: '修复', checked: 1, total: 2, found: 2, message: 'FC2-PPV-1.mp4',
  }} />);
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('修复 1 / 2 · FC2-PPV-1.mp4');
  await click(buttonNamed('停止', host));
  await settle();
  expect(sentBody(fetcher)).toEqual({ stop: true });
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('修好 2 部');
  expect(buttonNamed('开始修复', host)).not.toBeNull();
});

it('一部都没找到时说清楚这个库里的片子都能直接播', async () => {
  vi.useFakeTimers();
  const host = await mount(<MediaRepair initialLibraries={libraries}
    initial={{ ...idle, status: 'complete', library: '网盘', stage: '完成' }} />);
  expect(host.textContent).toContain('这个库里的片子都能直接播');
});

it('缺索引的片子卡在没装 untrunc 上时，指明去运行信息里下载', async () => {
  vi.useFakeTimers();
  const host = await mount(<MediaRepair initialLibraries={libraries} initial={{
    ...idle, status: 'complete', library: '网盘', stage: '完成', found: 2, failed: 2, missing_tool: 2,
  }} />);
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('修好 0 部，2 部修不了');
  expect(host.textContent).toContain('2 部缺索引的片子要装上 untrunc 才修得了');
});
