/* React 子树的构建配置：`web/dist/peach-react.js` 与 `web/dist/peach-react.css`。
 *
 * 和 `vite.config.ts` 分开构建，Preact 那份产物里就没有 React：island 按
 * `@peach/react` 引用这份产物，构建时改写成 `/dist/peach-react.js`，只有挂到 React 子树时
 * 浏览器才去取它。`npm run build` 先跑 Preact 那份（它会清空 web/dist），再跑这份。
 *
 * `@/` 指向 `src/react/boardui/`，上游 BoardUI 源码里的 `@/utils/cx` 因此原样成立。 */
import { fileURLToPath } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

import { LEGACY_MODULES } from './vite.config.ts';

export default defineConfig({
  plugins: [tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src/react/boardui', import.meta.url)) },
  },
  // 库模式不替换 `process.env.NODE_ENV`，React 会在浏览器里读到一个不存在的 `process`。
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: '../web/dist',
    emptyOutDir: false,
    target: 'es2022',
    // CSS 目标对齐 Tailwind v4 的浏览器基线。按 es2022 推出的目标偏旧，lightningcss 会给每个
    // oklch 颜色补一份 lab() 回退，末位小数随平台浮点不同，CI 的 Linux 重建就对不上提交的产物。
    cssTarget: ['chrome111', 'edge111', 'firefox128', 'safari16.4', 'ios16.4'],
    minify: 'oxc',
    sourcemap: false,
    cssCodeSplit: false,
    lib: {
      entry: 'src/react/entry.tsx',
      formats: ['es'],
      fileName: () => 'peach-react.js',
    },
    rollupOptions: {
      external: Object.keys(LEGACY_MODULES),
      output: {
        paths: LEGACY_MODULES,
        codeSplitting: false,
        assetFileNames: 'peach-react.[ext]',
      },
    },
  },
});
