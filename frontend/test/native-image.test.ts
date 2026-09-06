import { describe, expect, it } from 'vitest';
import { nativeImageFit, matchesFaceSource } from '../src/native-image';

it('544×724 的旧人像不能使用 2184×1468 封面的焦点', () => {
  expect(matchesFaceSource(544, 724, 2184, 1468)).toBe(false);
  expect(matchesFaceSource(544, 724, 544, 724)).toBe(true);
  expect(matchesFaceSource(0, 0, 0, 0)).toBe(false);
});

describe('头像和标识的小图补底', () => {
  it('大框中的低分辨率图片按原尺寸居中', () => {
    expect(nativeImageFit(64, 64, 180, 240)).toEqual({ small: true, width: 64, height: 64 });
  });
  it('70 px 紧凑头像适用，32 px 图标不补底', () => {
    expect(nativeImageFit(16, 16, 70, 70).small).toBe(true);
    expect(nativeImageFit(16, 16, 32, 32).small).toBe(false);
  });
  it('宽字标保持比例且不超出容器', () => {
    expect(nativeImageFit(400, 40, 180, 180)).toEqual({ small: true, width: 180, height: 18 });
  });
  it('高像素密度屏幕上的 64 px 方标允许在紧凑模式放大', () => {
    expect(nativeImageFit(64, 64, 70, 70, 2)).toEqual({ small: false, width: 32, height: 32 });
    expect(nativeImageFit(64, 64, 32, 32, 2).small).toBe(false);
  });
  it('清晰图片和只需轻微放大的图片铺满', () => {
    expect(nativeImageFit(300, 400, 180, 240).small).toBe(false);
    expect(nativeImageFit(350, 350, 369, 369, 2).small).toBe(false);
    expect(nativeImageFit(150, 200, 180, 240).small).toBe(false);
    expect(nativeImageFit(0, 0, 180, 240).small).toBe(false);
  });
});
