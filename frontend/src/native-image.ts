/** 64 px 以下的头像属于小图标；大图和 70 px 紧凑头像按源像素判断是否补底。 */
export function nativeImageFit(width: number, height: number, frameWidth: number, frameHeight: number, dpr = 1) {
  const density = Number.isFinite(dpr) && dpr > 0 ? dpr : 1;
  width /= density;
  height /= density;
  const valid = [width, height, frameWidth, frameHeight].every(value => Number.isFinite(value) && value > 0);
  const small = valid && Math.min(frameWidth, frameHeight) >= 64
    && (width < frameWidth * .4 || height < frameHeight * .4);
  const scale = valid ? Math.min(1, frameWidth / width, frameHeight / height) : 1;
  return { small, width: width * scale, height: height * scale };
}
