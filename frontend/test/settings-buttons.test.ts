/* 设置页的按钮：保存键一律叫「保存配置」，操作键用 BoardUI `Button` 的主按钮（`variant` 缺省即
 * `primary`，蓝底白字）。次按钮 `secondary` 只留给图标选择面板的触发键和「取消」，危险操作用 `danger`。 */
import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { expect, it } from 'vitest';

const dir = resolve(process.cwd(), 'src/react/settings');
const buttons = readdirSync(dir)
  .filter((name) => name.endsWith('.tsx'))
  .flatMap((name) => [...readFileSync(resolve(dir, name), 'utf8').matchAll(/<Button\b([\s\S]*?)<\/Button>/g)]
    .map(([, tag = '']) => ({ name, tag, label: tag.slice(tag.lastIndexOf('>') + 1).trim() })));

it('保存键一律叫「保存配置」', () => {
  const saves = buttons.filter((button) => button.label.startsWith('保存'));
  expect(saves.length).toBeGreaterThan(0);
  expect(saves.filter((button) => button.label !== '保存配置').map((button) => `${button.name}: ${button.label}`)).toEqual([]);
});

it('保存、检查、添加、刷新这类操作键都是主按钮', () => {
  const actions = buttons.filter((button) => /^(保存|检查|添加|刷新)/.test(button.label));
  expect(actions.map((button) => button.label)).toEqual(expect.arrayContaining(['保存配置', '检查更新', '添加文件夹', '刷新挂载状态']));
  expect(actions.filter((button) => /\bvariant=/.test(button.tag)).map((button) => `${button.name}: ${button.label}`)).toEqual([]);
});

it('次按钮只出现在图标选择面板', () => {
  const secondary = buttons.filter((button) => button.tag.includes('variant="secondary"'));
  expect([...new Set(secondary.map((button) => button.name))]).toEqual(['library-icon-picker.tsx']);
});
