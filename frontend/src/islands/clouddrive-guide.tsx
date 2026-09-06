import { useLayoutEffect, useRef } from 'preact/hooks';
import { wireCollapse } from '@peach/legacy/ui';

export const CLOUDDRIVE_PROFILES = [
  {name: '机械硬盘或内存不超过 8 GB', cache: '10–20 GiB', read: '256 / 128 KB', task: '同时处理 1 个视频', advice: '缓存优先放内置 SSD。只有机械硬盘时，先用按需读取；反复观看同一批文件才开启文件夹缓存。'},
  {name: 'SATA SSD，8–16 GB 内存', cache: '20–50 GiB', read: '256 / 128 KB', task: '同时处理 1–2 个视频', advice: '扫描、抽帧用小读块。观看高码率视频若仍缓冲，再试 512 / 256 KB。'},
  {name: 'NVMe SSD，16 GB 以上内存', cache: '50–100 GiB', read: '256 / 128 KB', task: '同时处理 2 个视频起步', advice: '以扫描和拖动播放为主时保留小读块。连续看高码率视频可试 512 / 256 KB，速度不升就调回。'},
] as const;

export function CloudDriveGuide() {
  const root = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => { if (root.current) wireCollapse(root.current, 'details', 'clouddrive-guide'); }, []);
  return <div ref={root} class="cloudguide">
    <p class="confighelp">先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。<a class="externallink" href="https://www.clouddrive2.com/help.html" target="_blank" rel="noreferrer">挂载帮助<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a></p>
    <details>
      <summary>CloudDrive 速度与缓存建议</summary>
      <p class="confighelp">按缓存所在的硬盘选起步配置。优先保证播放流畅，再用同一视频比较冷启动、拖动和流量；参数越大不一定越快。</p>
      <div class="cloudguide-profiles">{CLOUDDRIVE_PROFILES.map(profile => <section aria-label={profile.name} key={profile.name}>
        <h4>{profile.name}</h4>
        <dl><dt>磁盘缓存上限</dt><dd>{profile.cache}</dd><dt>默认 / 最小读取长度</dt><dd>{profile.read}</dd><dt>Peach 并行任务</dt><dd>{profile.task}</dd></dl>
        <p class="confighelp">{profile.advice}</p>
      </section>)}</div>
      <ul class="cloudguide-notes">
        <li>在 CloudDrive「设置」中设置磁盘缓存上限和 LRU（优先清理最久没用的缓存）。系统盘至少留 40 GiB；上限不要填 0。设置后重新打开确认，并观察实际占盘。</li>
        <li>在各网盘的下载设置中调整读取长度和下载线程。115 从 2 线程开始，遵守当前客户端上限；PikPak / WebDAV 从 2 线程开始，带宽充足且速度确实提升时再试 4。开启支持的直链选项，确认播放可用。</li>
        <li>PikPak 按当前 CloudDrive 提供的接入方式配置；使用 WebDAV 时，先确认服务端允许直链。不能直接套用 115 的连接方式。</li>
        <li>看视频时暂停批量抽帧，关闭不用的播放页。下载速度应高于视频码率除以 8，并留出余量：80 Mbps 视频约需 10 MB/s，建议稳定达到 15 MB/s。</li>
        <li>Buffer Cache 的内存占用、磁盘缓存和文件夹缓存是不同设置。磁盘显示的逻辑大小也不等于实际占盘；只改一个上限不能限制所有缓存。</li>
      </ul>
      <p class="confighelp">上表容量和并发是起步建议，按实际占盘与播放结果调整。直链和代理是不同设置；连接慢时分别比较，不能只看开关是否开启。<a class="externallink" href="https://www.clouddrive2.com/features.html" target="_blank" rel="noreferrer">缓存说明<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a></p>
    </details>
  </div>;
}
