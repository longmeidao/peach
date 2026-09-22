import { expect, it, vi } from 'vitest';

import { GeneralSettings } from '../../src/react/settings/general-settings';
import type { ConfigurationData, EntryLinksState } from '../../src/react/bundle';
import { buttonNamed, click, fetchMock, mount, sentBody, settle, submit, switches, type } from './render';

const data = (over: Partial<ConfigurationData> = {}): ConfigurationData => ({
  editable: true, notice: '', revision: 'rev-1', media_dirs: [], port: 9123, facts: [], ...over,
});

const state: EntryLinksState = {
  sites: [
    { key: 'javdb', label: 'JavDB', placeholder: 'javdb_id', enabled: true,
      template: 'https://javdb.com/actors/{javdb_id}?sort_type=4',
      default_template: 'https://javdb.com/actors/{javdb_id}?sort_type=4' },
    { key: 'minnano-av', label: 'minnano-av', placeholder: 'minnano_id', enabled: true,
      template: 'https://www.minnano-av.com/actress{minnano_id}.html',
      default_template: 'https://www.minnano-av.com/actress{minnano_id}.html' },
    { key: 'missav', label: 'MISSAV', placeholder: 'name', enabled: false,
      template: 'https://missav.ws/dm42/cn/actresses/{name}',
      default_template: 'https://missav.ws/dm42/cn/actresses/{name}' },
  ],
};

it('外部入口：三站各一颗开关与一条模板，保存发出开关与模板的实际值', async () => {
  const fetcher = fetchMock(200, state);
  vi.stubGlobal('fetch', fetcher);
  const receipt = vi.fn();
  const host = await mount(<GeneralSettings data={data({ entry_links: state })} receipt={receipt} />);
  expect(switches(host).map((input) => input.getAttribute('aria-label')))
    .toEqual(['在资料页显示 JavDB 入口', '在资料页显示 minnano-av 入口', '在资料页显示 MISSAV 入口']);
  expect(switches(host).map((input) => input.checked)).toEqual([true, true, false]);
  // 占位符按站给：提示里写错一个，改模板的人就会把服务端填不进去的名字写进地址。
  expect(host.textContent).toContain('用 {javdb_id} 占位');
  expect(host.textContent).toContain('用 {name} 占位');
  await click(switches(host)[2]);
  await type(host.querySelector('#entry-link-minnano-av'),
    'https://www.minnano-av.com/actress{minnano_id}.html?x=1');
  expect(fetcher).not.toHaveBeenCalled();
  await submit(host.querySelector('form'));
  await settle();
  expect(fetcher.mock.calls[0]?.[0]).toBe('/api/configuration/entry-links');
  expect(sentBody(fetcher)).toEqual({
    sites: {
      javdb: { enabled: true, template: 'https://javdb.com/actors/{javdb_id}?sort_type=4' },
      'minnano-av': { enabled: true, template: 'https://www.minnano-av.com/actress{minnano_id}.html?x=1' },
      missav: { enabled: true, template: 'https://missav.ws/dm42/cn/actresses/{name}' },
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
