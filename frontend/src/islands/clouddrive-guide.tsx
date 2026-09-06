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
      <summary>CloudDrive 速度与缓存建议</summary>
      <p class="confighelp">看缓存放在哪块硬盘上，照那一行填。先保证播放不卡，再拿同一个视频比较打开速度、拖动和流量；数值填得越大不一定越快。</p>
      <div class="cloudguide-tablewrap">
        <table class="cloudguide-table">
          <thead><tr><th scope="col">缓存所在硬盘</th><th scope="col">缓存上限</th><th scope="col">读取长度（默认 / 最小）</th><th scope="col">同时处理视频</th></tr></thead>
          <tbody>{CLOUDDRIVE_PROFILES.map(profile => <tr key={profile.name}>
            <th scope="row">{profile.name}</th><td>{profile.cache}</td><td>{profile.read}</td><td>{profile.task}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <ul class="cloudguide-notes">
        <li>缓存尽量放在内置固态盘上。只有机械硬盘时先用按需读取，反复看同一批文件才打开文件夹缓存。</li>
        <li>256 / 128 KB 适合扫描、抽帧和拖动播放。看高码率视频还是缓冲，就试 512 / 256 KB；速度没提上来就调回去。</li>
        <li>缓存上限和清理方式在 CloudDrive「设置」里填。清理方式选 LRU，也就是空间不够时先删最久没用过的缓存。上限不要填 0，系统盘至少留 40 GiB。填完重新打开这一页确认存住了，再看硬盘实际少了多少。</li>
        <li>读取长度和下载线程在每个网盘各自的下载设置里改，线程都从 2 开始。115 不要超过客户端标出的上限；PikPak 和 WebDAV 在带宽有余、加到 4 确实更快时才留 4。能开直链就开，开完放个视频确认还能播。</li>
        <li>PikPak 按 CloudDrive 当前提供的接入方式配置。走 WebDAV 时先确认服务端允许直链；115 的连接方式不能照搬过来。</li>
        <li>看视频时先暂停批量抽帧，关掉不用的播放页。码率按 Mbps 算，下载速度按 MB/s 算，除以 8 才能对上：80 Mbps 的视频要 10 MB/s 才够，留出余量建议稳定在 15 MB/s。</li>
        <li>Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，三处是分开的设置，改一个管不住另外两个。文件显示的大小是逻辑大小，也不等于真正占掉的盘。</li>
      </ul>
      <p class="confighelp">表里的容量和并发是起步值，按实际占盘和播放效果再调。直链和代理是两个开关，连接慢时分别试一次比较，不能只看开关有没有打开。<a class="externallink" href="https://www.clouddrive2.com/features.html" target="_blank" rel="noreferrer">缓存说明<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a></p>
    </details>
  </div>;
}
