import { describe, expect, it } from 'vitest';
import { javImageKind, normalizeJavImage, normalizeJavPreferences, posterBoxAnchor, syncJavImages } from '../src/jav-artwork';

describe('JAV 默认封面', () => {
  const jav = { is_jav: true, code: 'TEST-001', has_cover: true, has_thumb: true };
  it('默认官方封面，两档都按作品身份选择图片', () => {
    expect(normalizeJavImage(undefined)).toBe('cover');
    expect(normalizeJavImage('invalid')).toBe('cover');
    expect(javImageKind(jav, 'cover')).toBe('cover');
    expect(javImageKind(jav, 'thumbnail')).toBe('thumbnail');
    expect(javImageKind({ ...jav, is_jav: false }, 'cover')).toBe('thumbnail');
  });
  it('缺官方封面或预览图时使用可用图片，两者缺失时留空', () => {
    expect(javImageKind({ ...jav, has_cover: false }, 'cover')).toBe('thumbnail');
    expect(javImageKind({ ...jav, code: '' }, 'cover')).toBe('thumbnail');
    expect(javImageKind({ ...jav, has_thumb: false }, 'thumbnail')).toBe('cover');
    expect(javImageKind({ ...jav, has_cover: false, has_thumb: false }, 'cover')).toBe('');
  });
  it('原地更新多个表面的图片并可切回，保留播放器和节点', () => {
    const root = document.createElement('div');
    root.innerHTML = '<video></video>' + ['big', 'small'].map(layout =>
      `<img data-jav-image="1" data-jav-cover="/cover?code=TEST-001" data-jav-thumb="/poster?id=1&c=4" data-jav-image-layout="${layout}" class="poster" src="/poster?id=1&c=4">`).join('');
    const images = [...root.querySelectorAll('img')];
    const video = root.querySelector('video');
    syncJavImages(root, 'cover');
    expect(images.every(img => img.classList.contains('cover'))).toBe(true);
    expect(images[0]?.classList.contains('front')).toBe(true);
    expect(images[1]?.classList.contains('whole')).toBe(true);
    syncJavImages(root, 'thumbnail');
    expect(images.every(img => img.getAttribute('src') === '/poster?id=1&c=4' && !img.classList.contains('cover'))).toBe(true);
    expect(root.querySelector('video')).toBe(video);
    expect([...root.querySelectorAll('img')]).toEqual(images);
  });
  it.each(['big', 'small'])('%s 保留两种封面来源，保存后恢复同一组合', javLayout => {
    for (const javImage of ['cover', 'thumbnail']) {
      const settings = normalizeJavPreferences({ javLayout, javImage });
      expect(settings).toEqual({ javLayout, javImage });
      expect(normalizeJavPreferences(JSON.parse(JSON.stringify(settings)))).toEqual(settings);
      expect(javImageKind(jav, settings.javImage)).toBe(javImage);
    }
  });
  it('沿用已存版式与预览图选择，未知值使用默认值', () => {
    expect(normalizeJavPreferences({ javLayout: 'preview', javImage: 'cover' })).toEqual({ javLayout: 'small', javImage: 'thumbnail' });
    expect(normalizeJavPreferences({ javLayout: 'sleeve' })).toEqual({ javLayout: 'small', javImage: 'cover' });
    expect(normalizeJavPreferences({ javLayout: 'cover' })).toEqual({ javLayout: 'big', javImage: 'cover' });
    expect(normalizeJavPreferences({ javLayout: 'invalid', javImage: 'invalid' })).toEqual({ javLayout: 'big', javImage: 'cover' });
  });
});

/* 大图版式的容器比例，与 `web/app.js` 的 `COVER_FRONT_RATIO` 同一个值。
   它是常量不是变量，所以这里写字面量而不是从 app.js 里取——那份是无构建的旧层，
   引进来只会把整个页面壳拖进单测。 */
const BIG_LAYOUT_RATIO = 0.7;

describe('正封取景框换算成横向锚点', () => {
  it('沿折痕的框按可见窗口换算，窗口宽度由容器比例和源图高度定', () => {
    // 1600×1000 的封套，折痕右侧那块 2:3 正封从 887 开始。可见窗口 1000×0.7=700
    // 源图像素，可推的余量 1600−700=900，锚点 887/900。
    const fold = { x0: 887, y0: 0, x1: 1553, y1: 999, method: 'fold', px: [1600, 1000] };
    expect(posterBoxAnchor(fold, BIG_LAYOUT_RATIO)).toBe(98.56);
    // 容器换一个比例，窗口跟着变宽变窄：同一个框算出的锚点必须跟着动。
    expect(posterBoxAnchor(fold, 0.5)).toBe(80.64);
  });

  it('右半居中的框走同一套算术，方法只是它的来路', () => {
    // 800×538 是本机封套最常见的尺寸；没找到折痕时正面从右半 400 开始，框宽 358。
    const half = { x0: 421, y0: 0, x1: 779, y1: 537, method: 'ratio', px: [800, 538] };
    expect(posterBoxAnchor(half, BIG_LAYOUT_RATIO)).toBe(99.43);
  });

  it('没有框时返回 null，调用方退回原来的取景', () => {
    // 本机 1014 张封面里 331 张判定为不裁，接口发的就是 null，这条路不能算出数来。
    expect(posterBoxAnchor(null, BIG_LAYOUT_RATIO)).toBeNull();
    expect(posterBoxAnchor(undefined, BIG_LAYOUT_RATIO)).toBeNull();
    expect(posterBoxAnchor({ x0: 421 }, BIG_LAYOUT_RATIO)).toBeNull();
    expect(posterBoxAnchor({ x0: Number.NaN, px: [800, 538] }, BIG_LAYOUT_RATIO)).toBeNull();
    expect(posterBoxAnchor({ x0: 421, px: [0, 0] }, BIG_LAYOUT_RATIO)).toBeNull();
    expect(posterBoxAnchor({ x0: 421, px: [800, 538] }, 0)).toBeNull();
  });

  it('锚点夹在 0 到 100 之间，框推不到的位置不许把图片外面推进来', () => {
    // 折痕落在中位数 0.5253 上时框起点 431，比余量 423.4 还靠右：窗口已经顶到
    // 右边缘，锚点只能是 100%，取景与算框之前一致。
    expect(posterBoxAnchor({ x0: 431, px: [800, 538] }, BIG_LAYOUT_RATIO)).toBe(100);
    expect(posterBoxAnchor({ x0: 0, px: [1600, 1000] }, BIG_LAYOUT_RATIO)).toBe(0);
    expect(posterBoxAnchor({ x0: -40, px: [1600, 1000] }, BIG_LAYOUT_RATIO)).toBe(0);
  });

  it('源图比容器更竖时缩放由宽度决定，整幅宽度可见就没有锚点可写', () => {
    // 600×1000 比 0.7 的容器还竖，`object-fit:cover` 缩放取 max(容器宽/源图宽,
    // 容器高/源图高) 的前一项，横向一个像素都不裁。
    expect(posterBoxAnchor({ x0: 120, px: [600, 1000] }, BIG_LAYOUT_RATIO)).toBeNull();
    // 分母正好是 0 的那条边界：窗口宽度恰等于源图宽度。
    expect(posterBoxAnchor({ x0: 887, px: [1600, 1000] }, 1.6)).toBeNull();
  });
});
