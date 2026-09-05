import { describe, it, expect, vi, afterEach } from 'vitest';
import { watchJob, followJobProgress } from '../src/jobs';

afterEach(() => { vi.useRealTimers(); sessionStorage.clear(); document.body.innerHTML = ''; });

describe('后台任务状态恢复', () => {
  it('页面重建后恢复来源进度并只接收一次完成回执', async () => {
    vi.useFakeTimers();
    const host = document.createElement('div'); document.body.append(host);
    const complete = vi.fn();
    let state = {status: 'running', job_id: 'same', checked: 1, total: 3,
      current: {label: '演示来源', attempt: 3, max_attempts: 5, retry_in: 2}};
    const mount = (element: HTMLElement) => followJobProgress({host: element,
      active: () => true, read: async () => state, busy: () => {}, complete,
      note: text => text, loading: text => text, progress: () => ''});
    mount(host); await vi.advanceTimersByTimeAsync(0);
    expect(host.textContent).toContain('1/3');
    expect(host.textContent).toContain('第 3/5 次尝试');
    host.remove();
    const fresh = document.createElement('div'); document.body.append(fresh);
    mount(fresh); await vi.advanceTimersByTimeAsync(0);
    expect(fresh.textContent).toContain('演示来源');
    state = {...state, status: 'complete', checked: 3};
    await vi.advanceTimersByTimeAsync(4000);
    expect(complete).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem('peach-follow-job')).toBeNull();
  });
  it('连接中断后继续读取相同任务直至终态', async () => {
    const states: string[] = [], waits: number[] = [];
    let calls = 0, failures = 0;
    await watchJob({ active: () => true,
      read: async () => { calls++; if (calls === 2) throw new Error('offline');
        return { status: calls < 3 ? 'running' : 'complete', job_id: 'one' }; },
      render: state => states.push(state.status),
      disconnected: () => { failures++; }, pause: async ms => { waits.push(ms); },
    });
    expect(states).toEqual(['running', 'complete']);
    expect(failures).toBe(1);
    expect(waits).toEqual([2000, 4000]);
  });
  it('离开页面后丢弃在途响应', async () => {
    let active = true, rendered = false;
    await watchJob({ active: () => active,
      read: async () => { active = false; return { status: 'running' }; },
      render: () => { rendered = true; }, disconnected: () => {},
    });
    expect(rendered).toBe(false);
  });
  it('首读恢复只交接一次运行任务', async () => {
    let calls = 0;
    await watchJob({ active: () => true, once: true,
      read: async () => { calls++; return { status: 'running' }; },
      render: () => {}, disconnected: () => {},
    });
    expect(calls).toBe(1);
  });
});
