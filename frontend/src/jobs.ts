/** 后台任务查询只重试读状态；启动和写入请求由调用方单次提交。 */
export interface JobState {
  status: string;
  job_id?: string;
  checked?: number;
  total?: number;
  older?: boolean;
  error?: string;
  current?: { label?: string; provider?: string; attempt?: number;
    max_attempts?: number; retry_in?: number };
}

export async function watchJob<T extends JobState>(options: {
  read: (signal: AbortSignal) => Promise<T>;
  active: () => boolean;
  render: (state: T) => void;
  disconnected: (error: unknown) => void;
  keepWatching?: boolean;
  once?: boolean;
  pause?: (ms: number) => Promise<void>;
}): Promise<void> {
  const pause = options.pause || (ms => new Promise(resolve => setTimeout(resolve, ms)));
  let failures = 0;
  while (options.active()) {
    let state: T;
    try {
      state = await options.read(AbortSignal.timeout(15000));
    } catch (error) {
      if (!options.active()) return;
      failures++;
      options.disconnected(error);
      await pause(Math.min(2000 * 2 ** Math.min(failures, 4), 30000));
      continue;
    }
    if (!options.active()) return;
    failures = 0;
    options.render(state);
    if (options.once) return;
    if (!options.keepWatching && state.status !== 'running') return;
    await pause(2000);
  }
}

export function followJobProgress(options: {
  host: HTMLElement;
  active: () => boolean;
  read: (signal: AbortSignal) => Promise<JobState>;
  busy: (running: boolean) => void;
  complete: (state: JobState) => void;
  note: (text: string) => string;
  loading: (text: string) => string;
  progress: (value: number, max: number) => string;
  storageKey?: string;
  title?: string;
  watchIdle?: boolean;
}): void {
  const panel = document.createElement('div');
  options.host.hidden = true;
  panel.dataset.followJob = '';
  panel.setAttribute('aria-live', 'polite');
  options.host.prepend(panel);
  const storageKey = options.storageKey || 'peach-follow-job';
  let tracked: string | undefined = sessionStorage.getItem(storageKey) || undefined;
  let settled = false;
  void watchJob({
    read: options.read,
    active: () => !settled && options.active() && panel.isConnected,
    keepWatching: options.watchIdle !== false,
    render: state => {
      const running = state.status === 'running';
      options.host.hidden = !running;
      options.busy(running);
      if (running) {
        tracked = state.job_id;
        if (tracked) sessionStorage.setItem(storageKey, tracked);
        const current = state.current;
        const attempt = (current?.attempt || 1) > 1
          ? ` · 第 ${current?.attempt}/${current?.max_attempts} 次尝试${current?.retry_in ? `，${current.retry_in} 秒后重试` : ''}` : '';
        const text = (options.title || (state.total
          ? `${state.older ? '抓取历史' : '检查更新'}：已完成 ${state.checked || 0}/${state.total} 个来源`
          : '正在准备检查任务…'))
          + (current ? ` · ${current.label || current.provider || ''}${attempt}` : '');
        panel.innerHTML = options.loading(text)
          + ((state.total || 0) > 0 ? options.progress(state.checked || 0, state.total!) : '');
      } else if (tracked && tracked === state.job_id) {
        tracked = undefined;
        settled = true;
        options.host.hidden = state.status !== 'failed';
        sessionStorage.removeItem(storageKey);
        panel.innerHTML = state.status === 'failed' ? options.note(state.error || '检查失败') : '';
        options.complete(state);
      } else {
        if (tracked && state.status === 'idle') {
          options.host.hidden = false;
          panel.innerHTML = options.note('任务状态已失效，请重新发起任务');
          sessionStorage.removeItem(storageKey);
          settled = true;
          return;
        }
        panel.innerHTML = '';
      }
    },
    disconnected: () => {
      options.host.hidden = false;
      panel.innerHTML = options.note('暂时无法读取进度，正在重新连接…');
    },
  });
}
