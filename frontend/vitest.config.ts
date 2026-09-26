/* 测试配置和构建配置分开：`resolve.alias` 会同时作用于构建，
 * 把遗留模块的桩打进产物里——那正是 `build.rollupOptions.external` 要避免的。 */
import { fileURLToPath } from 'node:url';

import { defineConfig, mergeConfig } from 'vitest/config';

import base from './vite.config.ts';

const stub = (name: string) => fileURLToPath(new URL(`./test/stubs/${name}`, import.meta.url));
const source = (path: string) => fileURLToPath(new URL(`./src/${path}`, import.meta.url));

export default mergeConfig(base, defineConfig({
  resolve: {
    alias: {
      '@peach/legacy/core': stub('legacy-core.ts'),
      '@peach/legacy/ui': stub('legacy-ui.ts'),
      // 测试里 island 直接拿到 React 子树的源码入口，不经过 web/dist 产物。
      '@peach/react': source('react/entry.tsx'),
      '@/registry': source('react/evilcharts/registry'),
      '@/lib/utils': source('react/charts/cn.ts'),
      '@': source('react/boardui'),
    },
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.test.ts', 'test/**/*.test.tsx'],
    // 受限 runner 与本机资源守卫都给整棵测试进程树留固定预算；默认按 CPU 数扩张会耗尽进程槽。
    maxWorkers: 4,
    restoreMocks: true,
  },
}));
