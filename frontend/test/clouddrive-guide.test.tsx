import { render } from 'preact';
import { expect, it, vi } from 'vitest';
import { CloudDriveGuide } from '../src/islands/clouddrive-guide';
import { Configuration } from '../src/islands/configuration';

it('配置与首次设置共用按硬盘分档的建议，并链接官方说明', () => {
  const host=document.createElement('div');document.body.append(host);
  render(<CloudDriveGuide />,host);
  expect(host.querySelectorAll('.cloudguide-table tbody tr')).toHaveLength(3);
  expect([...host.querySelectorAll('.cloudguide-table thead th')].map(th=>th.textContent)).toEqual(['缓存所在硬盘','缓存上限','读取长度（默认 / 最小）','同时处理视频']);
  expect([...host.querySelectorAll('.cloudguide-table tbody th')].every(th=>th.getAttribute('scope')==='row')).toBe(true);
  expect(host.textContent).toContain('256 / 128 KB');
  expect(host.textContent).toContain('上限不要填 0');
  expect(host.querySelector('details')?.open).toBe(false);
  // 页内只留「填哪里、填多少、怎么确认」，换算与取证在仓库那一份文档里，所以这里必有它的链接。
  expect([...host.querySelectorAll('a')].map(a=>a.href)).toEqual([
    'https://www.clouddrive2.com/help.html',
    'https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md',
  ]);
  const data={editable:true,notice:'',revision:'test',media_dirs:['B:\\Media'],media_sources:[{location:'115',root:'B:\\',path:'B:\\Media'}],port:9123,facts:[]};
  render(<Configuration data={data} error="" receipt={vi.fn()} />,host);
  expect(host.querySelector('.cloudguide')).not.toBeNull();
  render(<Configuration key="local" data={{...data,media_sources:[{location:'local',root:'R:\\',path:'R:\\Media'}]}} error="" receipt={vi.fn()} />,host);
  expect(host.querySelector('.cloudguide')).toBeNull();host.remove();
});
