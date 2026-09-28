/* Video.js 的按需加载器。
 *
 * 和灯箱的 Swiper 同一个理由：video.js 676KB，只有真的开始看片才用得上，进首屏就是每次开页
 * 都白下一遍。主脚本与语言包有依赖——`videojs.addLanguage` 得先有 videojs——必须串行，不能
 * `Promise.all`。版本钉在这里与 `web/index.html` 的样式表上，`tests/test_dependency_policy.py`
 * 两侧都核。 */
import type { VideojsFactory } from './types';

const VIDEOJS = '/vendor/videojs/8.24.1/';

const loadScript = (src: string): Promise<void> => new Promise((resolve, reject) => {
  /* 两份产物（`peach-ui.js` 与 `peach-react.js`）各带一份这个加载器：另一份已经插过的脚本
     不再插第二次，等它自己落地；已经落地的（`data-loaded`）不会再发 `load`，直接算好。 */
  const existing = document.head.querySelector<HTMLScriptElement>(`script[src="${src}"]`);
  if (existing?.dataset.loaded) { resolve(); return }
  const script = existing ?? document.createElement('script');
  script.addEventListener('load', () => { script.dataset.loaded = '1'; resolve() }, { once: true });
  script.addEventListener('error', () => { script.remove(); reject(new Error(`script unavailable: ${src}`)) }, { once: true });
  if (!existing) { script.src = src; document.head.appendChild(script) }
});

const current = (): VideojsFactory | undefined => (globalThis as { videojs?: VideojsFactory }).videojs;

let loader: Promise<VideojsFactory> | null = null;

/** 取全局 `videojs`；没有就按顺序装主脚本与中文语言包。失败把加载器清空，一次网络抖动之后
 *  这一整页还挂得上播放器。 */
export function ensureVideojs(): Promise<VideojsFactory> {
  const ready = current();
  if (ready) return Promise.resolve(ready);
  loader ??= loadScript(`${VIDEOJS}video.min.js`)
    .then(() => loadScript(`${VIDEOJS}lang/zh-CN.js`))
    .then(() => {
      const factory = current();
      if (!factory) throw new Error('videojs unavailable');
      return factory;
    })
    .catch((error: unknown) => { loader = null; throw error });
  return loader;
}
