/* `/js/home-glow.js` 的类型声明：光晕的参数模型、预设与色板，壳与设置面板读同一份。
 * 只声明 TypeScript 这一侧用得到的那几样。 */
interface GlowSpot { color: string; alpha: number }
/** 一份光晕设置；形状与 `settings-panel-api.ts` 的 `HomeGlow` 相同。 */
interface HomeGlow {
  on: boolean; preset: string; strength: number; noise: number; speed: number; soften: number; size: number;
  spot1: GlowSpot; spot2: GlowSpot; spot3: GlowSpot;
}

export declare const HOME_GLOW_SPOTS: readonly ('spot1' | 'spot2' | 'spot3')[];
export declare const GLOW_SPOT_LABELS: readonly string[];
/** `[色系, 名称]`，第一项是「全部」。 */
export declare const GLOW_SWATCH_FAMILIES: readonly (readonly [key: string, label: string])[];
/** `[色系, 名称, #rrggbb]`。 */
export declare const GLOW_SWATCHES: readonly (readonly [family: string, name: string, hex: string])[];
/** 合法的 `#rrggbb` 转成小写原样返回，否则给 `fallback`。 */
export declare function glowColor(value: unknown, fallback: string): string;
export declare function glowPresetName(key: string): string;
/** 「玻璃原色」那一档：没有三枚光晕，面上漂的是每块玻璃自带的两团反光。 */
export declare function isNativeGlass(key: string): boolean;
/** 读回存量时的规范化；给 null 得到出厂那一套。 */
export declare function normalizeHomeGlow(raw: unknown): HomeGlow;
