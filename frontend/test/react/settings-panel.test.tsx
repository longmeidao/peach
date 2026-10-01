/* 设置面板（`settings-panel` 岛）与壳之间的接缝：每一项改完只落一次盘、只报自己那一个效果名，
 * 拉条拖动中只排重画、松手才落盘，面板 DOM 只建一次。开合、焦点、写接口与像素在真浏览器里验，
 * 见 `e2e/settings-panel.test.ts` 与 `e2e/design.test.ts`。 */
import { act } from 'react';
import { notifyManager } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import { normalizeHomeGlow } from '@peach/legacy/home-glow';

import { queryClient } from '../../src/react/query';
import { configureSettingsPanel } from '../../src/react/settings-panel/settings-panel';
import type { PanelSettings, SettingsEffect, SettingsPanelApi } from '../../src/react/settings-panel/settings-panel-api';
import { createSettingsStore } from '../../src/settings-store';

import { click, settle } from './render';

notifyManager.setScheduler((notify) => notify());

interface Stage {
  api: SettingsPanelApi;
  changed: Mock<(effect: SettingsEffect) => void>;
  save: Mock<() => void>;
  value: PanelSettings;
}

const settings = (): PanelSettings => ({
  theme: 'system', uiSounds: true, homeGlow: { ...normalizeHomeGlow(null), on: true, preset: 'ash' },
  sidebarOrder: [''], batchSize: 60, defaultSort: 'seed', defaultSortDirection: '', groupCollapse: true,
  javImage: 'cover', feedAutoScroll: true, feedHideGroupCompilations: true, feedHideSoloCompilations: false,
  feedHideExcerpts: true, hoverDelaySeconds: 5, detailAutoplay: false, miniplayer: true, seekSeconds: 10,
  relatedLimit: 24, searchHistoryLimit: 10, followInitialDays: 30, metadataRefreshDays: 30,
});

function stage(): Stage {
  const value = settings();
  const store = createSettingsStore('peach.settings.v1', value);
  const save = vi.spyOn(store, 'save') as unknown as Mock<() => void>;
  const changed = vi.fn<(effect: SettingsEffect) => void>();
  const api = configureSettingsPanel({
    store, changed, sound: () => {},
    navCatalog: [['', '首页', 'house']],
    themeOptions: [['system', '跟随系统', 'monitor'], ['light', '浅色', 'sun'], ['dark', '深色', 'moon']],
    videoLayouts: [['small', '小'], ['large', '大']],
    followInitialRanges: [['30', '30 天']],
    videoLayout: () => 'small', setVideoLayout: () => {},
    censored: () => false, setCensored: () => {}, highContrast: () => false, setHighContrast: () => {},
    renderGlowGrid: () => {}, wireGlowGrid: () => {},
    receipt: () => {}, failure: () => {}, syncRemote: () => {}, openConfiguration: () => {}, attached: () => {},
    configurable: async () => false,
  });
  return { api, changed, save, value };
}

const effects = (changed: Stage['changed']) => changed.mock.calls.map(([effect]) => effect);

beforeEach(() => {
  /* 不放动画：关上当场收起。 */
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: query.includes('reduce'), media: query, addEventListener: () => {}, removeEventListener: () => {},
  }));
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) })));
});

afterEach(async () => {
  queryClient.clear();
});

async function open(current: Stage, section?: string): Promise<HTMLElement> {
  await act(async () => current.api.open(section));
  await settle();
  return document.querySelector<HTMLElement>('#settingsPanel')!;
}

async function close(current: Stage): Promise<void> {
  await act(async () => current.api.close());
  await settle();
}

describe('设置面板与壳的接缝', () => {
  it('每一个开关只落一次盘、只报自己那一个效果名', async () => {
    const current = stage();
    const panel = await open(current);
    for (const [id, field, effect] of [
      ['uiSoundsSetting', 'uiSounds', 'uiSounds'], ['groupCollapseSetting', 'groupCollapse', 'groupCollapse'],
      ['miniplayerSetting', 'miniplayer', 'miniplayer'], ['feedAutoScrollSetting', 'feedAutoScroll', 'feedAutoScroll'],
    ] as const) {
      current.changed.mockClear();
      current.save.mockClear();
      await click(panel.querySelector(`#${id}`));
      expect([current.value[field], current.save.mock.calls.length, effects(current.changed)], id)
        .toEqual([false, 1, [effect]]);
    }
    /* 详情自动播放没有壳那一侧要跟着做的事：只落盘，不报效果。 */
    current.changed.mockClear();
    await click(panel.querySelector('#detailAutoplaySetting'));
    expect([current.value.detailAutoplay, effects(current.changed)]).toEqual([true, []]);

    current.changed.mockClear();
    await click(panel.querySelector('#themeSetting input[value="dark"]'));
    expect([current.value.theme, effects(current.changed)]).toEqual(['dark', ['theme']]);
    await close(current);
  });

  it('拖动光晕拉条：每一步只叫壳排一帧重画，不落盘；松手那一下才落盘', async () => {
    const current = stage();
    const panel = await open(current);
    const root = panel.querySelector<HTMLElement>('[data-glow-dial="strength"]')!;
    const slider = root.querySelector<HTMLElement>('[data-dial-slider]')!;
    root.querySelector<HTMLElement>('.dial-track')!.getBoundingClientRect = () =>
      ({ left: 0, top: 0, right: 100, bottom: 10, width: 100, height: 10, x: 0, y: 0, toJSON: () => ({}) });
    current.changed.mockClear();
    current.save.mockClear();
    const pointer = (type: string, clientX: number) =>
      slider.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX, button: 0 }));
    await act(async () => {
      pointer('pointerdown', 10);
      pointer('pointermove', 20);
      pointer('pointermove', 30);
    });
    expect(current.save).not.toHaveBeenCalled();
    expect(effects(current.changed)).toEqual(['glowFrame', 'glowFrame', 'glowFrame']);
    expect(current.value.homeGlow.strength).toBe(30);
    await act(async () => { pointer('pointerup', 30) });
    expect(current.save).toHaveBeenCalledTimes(1);
    expect(effects(current.changed)).toEqual(['glowFrame', 'glowFrame', 'glowFrame']);
    await close(current);
  });

  it('关上再开是同一棵面板：DOM 只建一次，光晕参数区不重建', async () => {
    const current = stage();
    const panel = await open(current);
    const glow = panel.querySelector('#homeGlowControls');
    const dial = panel.querySelector('[data-glow-dial="speed"]');
    await close(current);
    expect(panel.hidden).toBe(true);
    const again = await open(current, '浏览');
    expect(document.querySelectorAll('[data-settings-host]')).toHaveLength(1);
    expect(again).toBe(panel);
    expect(again.querySelector('#homeGlowControls')).toBe(glow);
    expect(again.querySelector('[data-glow-dial="speed"]')).toBe(dial);
    await close(current);
  });
});
