import { expect, it, vi } from 'vitest';

import { GeneralSettings } from '../../src/react/settings/general-settings';
import type { ConfigurationData, EntryLinksState } from '../../src/react/bundle';
import { buttonNamed, click, fetchMock, mount, sentBody, settle, submit, switches, type } from './render';

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true, notice: '', revision: 'rev-1', media_dirs: [], port: 9123, facts: [], ...over,
});

const state: EntryLinksState = {
  sites: [
    { key: 'javdb', label: 'JavDB', enabled: true, host: 'javdb.com', default_host: 'javdb.com' },
    { key: 'minnano-av', label: 'minnano-av', enabled: true, host: null, default_host: null },
    { key: 'missav', label: 'MISSAV', enabled: false, host: 'missav.ws', default_host: 'missav.ws' },
  ],
};

it('外部入口：三站各一颗开关，有镜像的两站各一个域名框，保存发出实际值', async () => {
  const fetcher = fetchMock(200, state);
  vi.stubGlobal('fetch', fetcher);
  const receipt = vi.fn();
  const host = await mount(<GeneralSettings data={data({ entry_links: state })} receipt={receipt} />);
  expect(switches(host).map((input) => input.getAttribute('aria-label')))
    .toEqual(['在资料页显示 JavDB 入口', '在资料页显示 minnano-av 入口', '在资料页显示 MISSAV 入口']);
  expect(switches(host).map((input) => input.checked)).toEqual([true, true, false]);
  // みんなのAV 只此一家，没有域名可换，那一行就不该出现一个填了也没用的框。
  expect(host.querySelector('#entry-link-minnano-av')).toBeNull();
  expect(host.textContent).toContain('只写域名本身，默认 javdb.com');
  await click(switches(host)[2]);
  await type(host.querySelector('#entry-link-javdb'), 'javdb521.com');
  expect(fetcher).not.toHaveBeenCalled();
  await submit(host.querySelector('form'));
  await settle();
  expect(fetcher.mock.calls[0]?.[0]).toBe('/api/configuration/entry-links');
  expect(sentBody(fetcher)).toEqual({
    sites: {
      javdb: { enabled: true, host: 'javdb521.com' },
      'minnano-av': { enabled: true },
      missav: { enabled: true, host: 'missav.ws' },
    },
  });
  expect(receipt).toHaveBeenCalledWith('已保存配置');
});

it('服务端没下发外部入口时通用组里不画这一节', async () => {
  // 站点清单由服务端给。前端自己兜一份默认的话，那份迟早和 `peach.entry_links` 分叉。
  const host = await mount(<GeneralSettings data={data()} receipt={vi.fn()} />);
  expect(host.textContent).not.toContain('外部入口');
  expect(buttonNamed('保存配置', host)).toBeNull();
});
