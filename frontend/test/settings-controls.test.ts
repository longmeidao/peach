import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {describe, it, expect, vi, afterEach} from 'vitest';

const source = readFileSync(resolve(process.cwd(), '../web/app.js'), 'utf8');
const armSource = source.match(/const armLong=(.*);/)![1];

describe('悬停放大设置', () => {
  afterEach(() => vi.useRealTimers());
  it('关闭时不启动计时，开启后按延迟放大', () => {
    vi.useFakeTimers();
    const card = document.createElement('div');
    const settings = {hoverDelaySeconds: 0};
    const arm = new Function('el', 'appSettings', `let longTimer; return ${armSource}`)(card, settings);
    arm();
    vi.advanceTimersByTime(10000);
    expect(card.className).toBe('');
    settings.hoverDelaySeconds = 3;
    arm();
    expect(card.classList.contains('previewing')).toBe(true);
    vi.advanceTimersByTime(2999);
    expect(card.classList.contains('longhover')).toBe(false);
    vi.advanceTimersByTime(1);
    expect(card.classList.contains('longhover')).toBe(true);
  });
  it('计时中关闭后不进入放大状态', () => {
    vi.useFakeTimers();
    const card = document.createElement('div');
    const settings = {hoverDelaySeconds: 3};
    const arm = new Function('el', 'appSettings', `let longTimer; return ${armSource}`)(card, settings);
    arm();
    settings.hoverDelaySeconds = 0;
    vi.advanceTimersByTime(3000);
    expect(card.classList.contains('longhover')).toBe(false);
  });
});
