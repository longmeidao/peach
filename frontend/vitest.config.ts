/* 测试配置和构建配置分开：`resolve.alias` 会同时作用于构建，
 * 把遗留模块的桩打进产物里——那正是 `build.rollupOptions.external` 要避免的。 */
import { fileURLToPath } from 'node:url';

import { defineConfig, mergeConfig } from 'vitest/config';

import base from './vite.config.ts';

const stub = (name: string) => fileURLToPath(new URL(`./test/stubs/${name}`, import.meta.url));

export default mergeConfig(base, defineConfig({
  resolve: {
    alias: {
      '@peach/legacy/core': stub('legacy-core.ts'),
      '@peach/legacy/ui': stub('legacy-ui.ts'),
    },
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.test.ts', 'test/**/*.test.tsx'],
    restoreMocks: true,
  },
}));
