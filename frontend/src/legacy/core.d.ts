/* `web/js/core.js` 的类型声明。
 *
 * 那份文件由 Peach 直接以 `/js/core.js` 提供，不进 bundle（见 vite.config.ts）。
 * 这里只声明 island 真正用到的导出：声明全集会在遗留层改动时假装类型仍然成立。
 * 迁移下一个页面时按需补，不要一次抄完。 */

/** 来源代号到界面名称：`local`→`本地`、`115`→`115`、`pikpak`→`PikPak`、`online`→`在线`。 */
export declare const LOC: Record<string, string>;

/** 秒数格式化成 `h:mm:ss`／`m:ss`；`0`、负数与非有限值都是 `—`（probe 的硬失败哨兵）。 */
export declare function fmtDur(seconds: number | null | undefined): string;

/** 字节格式化成 TB／GB／MB。 */
export declare function fmtSize(bytes: number | null | undefined): string;
