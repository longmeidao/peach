import { describe, expect, it } from 'vitest';
import { javImageKind, normalizeJavImage, syncJavImages } from '../src/jav-artwork';

describe('JAV 默认图片', () => {
  const jav = { is_jav: true, code: 'TEST-001', has_cover: true, has_thumb: true };
  it('默认封面，两档都按作品身份选择图片', () => {
    expect(normalizeJavImage(undefined)).toBe('cover');
    expect(normalizeJavImage('invalid')).toBe('cover');
    expect(javImageKind(jav, 'cover')).toBe('cover');
    expect(javImageKind(jav, 'thumbnail')).toBe('thumbnail');
    expect(javImageKind({ ...jav, is_jav: false }, 'cover')).toBe('thumbnail');
  });
  it('缺封面或缩略图时使用可用图片，两者缺失时留空', () => {
    expect(javImageKind({ ...jav, has_cover: false }, 'cover')).toBe('thumbnail');
    expect(javImageKind({ ...jav, code: '' }, 'cover')).toBe('thumbnail');
    expect(javImageKind({ ...jav, has_thumb: false }, 'thumbnail')).toBe('cover');
    expect(javImageKind({ ...jav, has_cover: false, has_thumb: false }, 'cover')).toBe('');
  });
  it('原地更新多个表面的图片并可切回，保留播放器和节点', () => {
    const root = document.createElement('div');
    root.innerHTML = '<video></video>' + ['big', 'small', 'preview'].map(layout =>
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
});
