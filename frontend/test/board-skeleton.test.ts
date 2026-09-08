import { describe, expect, it } from 'vitest';
import { boardPageSkeleton } from '../src/board-skeleton';

describe('Board 页面骨架', () => {
  it.each(['/stats', '/taste', '/follow-manage', '/configuration'])('为 %s 提供单一等待语义', path => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton(path);
    expect(root.querySelectorAll('[role="status"]')).toHaveLength(1);
    expect(root.querySelector('[aria-hidden="true"]')).not.toBeNull();
    expect(root.querySelectorAll('button, input, a')).toHaveLength(0);
  });
  it('统计预留四张指标卡，未知页面交给自身骨架', () => {
    const root = document.createElement('div');
    root.innerHTML = boardPageSkeleton('/stats');
    expect(root.querySelectorAll('.tastesummary')).toHaveLength(4);
    expect(boardPageSkeleton('/item/5')).toBe('');
  });
});
