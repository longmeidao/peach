import { useLayoutEffect, useRef } from 'preact/hooks';
import { wireCollapse } from '@peach/legacy/ui';

export const CLOUDDRIVE_PROFILES = [
  {name: '机械硬盘，或内存 8 GB 以内', cache: '10–20 GiB', read: '256 / 128 KB', task: '1 个'},
  {name: 'SATA SSD，内存 8–16 GB', cache: '20–50 GiB', read: '256 / 128 KB', task: '1–2 个'},
  {name: 'NVMe SSD，内存 16 GB 以上', cache: '50–100 GiB', read: '256 / 128 KB', task: '2 个起步'},
] as const;

export function CloudDriveGuide() {
  const root = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => { if (root.current) wireCollapse(root.current, 'details', 'clouddrive-guide'); }, []);
  return <div ref={root} class="cloudguide">
    <p class="confighelp">先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。<a class="externallink" href="https://www.clouddrive2.com/help.html" target="_blank" rel="noreferrer">挂载帮助<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a></p>
    <details>
      <summary><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right" /></svg>CloudDrive 速度与缓存建议</summary>
      <p class="confighelp">看缓存放在哪块硬盘上，照那一行填。表里是起步值，先保证播放不卡，再拿同一个视频比较打开速度、拖动和流量；填得越大不一定越快。</p>
      <div class="cloudguide-tablewrap">
        <table class="cloudguide-table">
          <thead><tr><th scope="col">缓存所在硬盘</th><th scope="col">缓存上限</th><th scope="col">读取长度（默认 / 最小）</th><th scope="col">同时处理视频</th></tr></thead>
          <tbody>{CLOUDDRIVE_PROFILES.map(profile => <tr key={profile.name}>
            <th scope="row">{profile.name}</th><td>{profile.cache}</td><td>{profile.read}</td><td>{profile.task}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <ul class="cloudguide-notes">
        <li>缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB。</li>
        <li>读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。看高码率视频还是缓冲就试 512 / 256 KB，打开速度、拖动和流量都没改善就调回去。</li>
        <li>Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，三处是分开的设置，改一个管不住另外两个。</li>
        <li>填完重新打开 CloudDrive 的设置页确认存住了，再看硬盘实际少了多少。播放期间先暂停批量抽帧、关掉不用的播放页。</li>
      </ul>
      <p class="confighelp">三处缓存分别管什么、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在<a class="externallink" href="https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md" target="_blank" rel="noreferrer">CloudDrive 配置与调优<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>。</p>
    </details>
  </div>;
}
