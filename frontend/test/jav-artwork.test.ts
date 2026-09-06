import { describe, expect, it } from 'vitest';
import { javImageKind, normalizeJavImage, normalizeJavPreferences, syncJavImages } from '../src/jav-artwork';

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
