/* Peach island 层的构建配置。
 *
 * 输出是**一个**确定名字的 ES module：`web/dist/peach-ui.js`。不加内容哈希，
 * 因为引用它的是 Peach 自己服务的 `web/app.js`（`await import('/dist/peach-ui.js')`），
 * 那份文件不经过任何构建，没法在构建时被改写；哈希文件名只会让它指向一个不存在的路径。
 * 缓存由服务端的 `Cache-Control: no-store` 负责，和 index.html／app.js 同一口径。
 *
 * 已经由 Peach 服务的遗留 ES module 保持外部依赖：它们在浏览器里是 `/js/*.js`，
 * 打进 bundle 会出现两份实现，`LOC`、`fmtDur` 这种语义契约就会各走一份。
 * 源码里用 `@peach/legacy/*` 引用，`output.paths` 在产物里改写回真实路径。
 */
import { defineConfig } from 'vite';

export const LEGACY_MODULES = {
  '@peach/legacy/core': '/js/core.js',
  '@peach/legacy/ui': '/js/ui-components.js',
} as const;

export default defineConfig({
  build: {
    outDir: '../web/dist',
    // 产物进 Git，所以目录必须只剩当前构建的东西；残留文件会被一起提交。
    emptyOutDir: true,
    target: 'es2022',
    // Vite 8 的内核是 rolldown，压缩走 oxc；写 'esbuild' 会落到已废弃的转译插件上。
    minify: 'oxc',
    sourcemap: false,
    cssCodeSplit: false,
    lib: {
      entry: 'src/islands.ts',
      formats: ['es'],
      fileName: () => 'peach-ui.js',
    },
    rollupOptions: {
      external: Object.keys(LEGACY_MODULES),
      output: {
        paths: LEGACY_MODULES,
        // island 之间不做代码分割：入口是浏览器直接 import 的单一模块。
        codeSplitting: false,
        assetFileNames: 'peach-ui.[ext]',
      },
    },
  },
});
