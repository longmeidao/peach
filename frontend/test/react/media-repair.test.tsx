import { expect, it, vi } from 'vitest';

import { MediaRepair, type MediaRepairState } from '../../src/react/settings/media-repair';
import { buttonNamed, click, fetchMock, mount, sentBody, settle } from './render';

const idle: MediaRepairState = {
  status: 'idle', stage: '', checked: 0, total: 0, found: 0, repaired: 0, failed: 0, skipped: 0, message: '',
};

it('开始修复把要不要连计费来源一起发过去，随后按服务端的进度报扫描到哪一部', async () => {
  vi.useFakeTimers();
  const fetcher = fetchMock(200, { ...idle, status: 'running', stage: '扫描', checked: 3, total: 12 });
  vi.stubGlobal('fetch', fetcher);
  const host = await mount(<MediaRepair initial={idle} />);
  await click(host.querySelector('input[type="checkbox"]'));
  await click(buttonNamed('开始修复', host));
  await settle();
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher.mock.calls[0]?.[0]).toBe('/api/media-repair');
  expect(sentBody(fetcher)).toEqual({ allow_metered: true, restart: true });
  expect(host.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow')).toBe('25');
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('扫描 3 / 12');
  expect(buttonNamed('停止', host)).not.toBeNull();
});

it('修复阶段点名当前这部片，停止之后回到可以再开始的样子', async () => {
  vi.useFakeTimers();
  const fetcher = fetchMock(200, { ...idle, status: 'complete', stage: '完成', repaired: 2 });
  vi.stubGlobal('fetch', fetcher);
  const host = await mount(<MediaRepair initial={{
    ...idle, status: 'running', stage: '修复', checked: 1, total: 2, found: 2, message: 'FC2-PPV-1.mp4',
  }} />);
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('修复 1 / 2 · FC2-PPV-1.mp4');
  await click(buttonNamed('停止', host));
  await settle();
  expect(sentBody(fetcher)).toEqual({ stop: true });
  expect(host.querySelector('p[role="status"]')?.textContent).toBe('修好 2 部');
  expect(buttonNamed('开始修复', host)).not.toBeNull();
});

it('一部都没找到时说清楚是库里的片子都能直接播', async () => {
  vi.useFakeTimers();
  const host = await mount(<MediaRepair initial={{ ...idle, status: 'complete', stage: '完成' }} />);
  expect(host.textContent).toContain('库里的片子都能直接播');
});
