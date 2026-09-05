/* 配置页（`/configuration`）：这台电脑的媒体文件夹与本机端口，加一块运行信息。
 *
 * 数据契约在 `/api/configuration`（`src/peach/routes_configuration.py`）。服务端按两道门
 * 放行：只有独立包、且只有从运行 Peach 的这台电脑打开时 `editable` 才为真；其它情况
 * 表单不画，只留一句为什么和运行信息。保存成功后 Peach 会重启，这里给一句持久 Note、
 * 一条新地址的链接，并在托盘换好进程后自己跳过去。
 *
 * 表单校验的原因由服务端按字段给（400 的 `errors`），页面把它们写回原位，不在前端
 * 复制一份路径与端口的判定。 */
import { useEffect, useLayoutEffect, useRef, useState } from 'preact/hooks';
import type { JSX } from 'preact';

import { fieldsetTitle, noteHtml, setActionBusy, selectFieldHtml, wireSelectField } from '@peach/legacy/ui';
import { ApiError, apiGet, apiSend, errorMessage } from '../api';

export interface ConfigurationProps {
  /** 保存成功后的过去时回执（遗留层的 Toast）。 */
  receipt(message: string): void;
}

export interface ConfigurationFact {
  term: string;
  value: string;
}

export interface ConfigurationData {
  editable: boolean;
  /** 不能编辑时给用户看的原因，可编辑时为空。 */
  notice: string;
  /** 设置文件的指纹，保存时带回去，服务端据此拒绝盖掉别处的改动。 */
  revision: string;
  media_dirs: string[];
  media_sources?: { location: string; root: string; path: string; online?: boolean }[];
  windows?: boolean;
  port: number;
  facts: ConfigurationFact[];
}

interface FieldErrors {
  media_dirs?: string[];
  port?: string;
}

interface SaveResult {
  saved: boolean;
  url: string;
  revision: string;
}

export const CONFIGURATION_URL = '/api/configuration';
/** 让运行 Peach 的这台电脑弹系统文件夹对话框；浏览器自己拿不到本机绝对路径。 */
export const PICK_FOLDER_URL = '/api/pick-folder';

/** 保存后等托盘换好进程再跳到新地址的时间。首启完成页用的是同一个数。 */
export const RESTART_REDIRECT_MS = 8000;

export const loadConfiguration = (
  _props: ConfigurationProps,
  signal: AbortSignal,
): Promise<ConfigurationData> => apiGet<ConfigurationData>(CONFIGURATION_URL, signal);

type State = { data: ConfigurationData | null; error: string };

const Html = ({ html, class: className }: { html: string; class?: string }) => (
  <div class={className} dangerouslySetInnerHTML={{ __html: html }} />
);

const fieldErrorsOf = (cause: unknown): FieldErrors | null => {
  if (!(cause instanceof ApiError) || cause.status !== 400) return null;
  const body = cause.body as { errors?: FieldErrors } | null;
  return body?.errors ?? null;
};

function Facts({ facts }: { facts: ConfigurationFact[] }) {
  return (
    <section class="configfieldset" data-geist-fieldset aria-labelledby="configFactsTitle">
      <div class="geist-fieldset-content">
        <Html html={fieldsetTitle('configFactsTitle', '运行信息')} />
        <dl class="configfacts">
          {facts.map((fact) => (
            <>
              <dt>{fact.term}</dt>
              <dd>{fact.value}</dd>
            </>
          ))}
        </dl>
      </div>
    </section>
  );
}

function MountStatus({ data }: { data: ConfigurationData }) {
  const [sources, setSources] = useState(data.media_sources);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const refresh = async (button: HTMLButtonElement) => {
    if (controller.current) return;
    const request = new AbortController(); controller.current = request;
    setActionBusy(button, true); setError('');
    try {
      const result = await apiGet<ConfigurationData>(CONFIGURATION_URL, request.signal);
      if (!request.signal.aborted) setSources(result.media_sources);
    } catch (cause) {
      if (!request.signal.aborted) setError(errorMessage(cause));
    } finally { controller.current = null; setActionBusy(button, false); }
  };
  if (!sources) return null;
  return <section class="configfieldset" aria-labelledby="configMountsTitle"><div class="geist-fieldset-content">
    <Html html={fieldsetTitle('configMountsTitle', '挂载状态')} />
    <dl class="configfacts">{sources.map((row) => <><dt>{({local: '本地磁盘', '115': 'CloudDrive · 115', pikpak: 'CloudDrive · PikPak'} as Record<string, string>)[row.location] || row.location}</dt><dd>{row.path || '未配置挂载点'} <span class={`configstatus ${row.online === true ? 'online' : row.online === false ? 'offline' : 'unknown'}`}>{row.online === true ? '在线' : row.online === false ? '离线' : '未检测'}</span></dd></>)}</dl>
    {error ? <p class="configbad" role="alert">{error}</p> : null}
    <button type="button" class="geist-button" onClick={(event) => refresh(event.currentTarget)}>刷新挂载状态</button>
  </div></section>;
}

function MediaSourceSelect({ value, label, onChange }: { value: string; label: string; onChange(value: string): void }) {
  const mount = useRef<HTMLDivElement>(null);
  const control = useRef<HTMLElement & { value: string; disabled: boolean } | null>(null);
  const callback = useRef(onChange);
  callback.current = onChange;
  useLayoutEffect(() => {
    const root = mount.current!;
    root.innerHTML = selectFieldHtml([['local', '本地磁盘'], ['115', 'CloudDrive · 115'], ['pikpak', 'CloudDrive · PikPak']], value, { label });
    const field = wireSelectField(root.firstElementChild!);
    control.current = field;
    const change = () => callback.current(field.value);
    field.addEventListener('change', change);
    return () => { control.current = null; field.disabled = true; field.removeEventListener('change', change); root.replaceChildren(); };
  }, [label]);
  useLayoutEffect(() => { if (control.current) control.current.value = value; }, [value]);
  return <div ref={mount} class="configsourcecontrol" />;
}

function ConfigurationForm({ data, receipt }: { data: ConfigurationData; receipt: ConfigurationProps['receipt'] }) {
  const initial = data.media_sources?.filter((row) => ['local', '115', 'pikpak'].includes(row.location));
  const [dirs, setDirs] = useState<string[]>(initial?.length ? initial.map((row) => row.path) : data.media_dirs.length ? data.media_dirs : ['']);
  const [kinds, setKinds] = useState<string[]>(initial?.map((row) => row.location) ?? []);
  const [roots, setRoots] = useState<string[]>(initial?.map((row) => row.root) ?? []);
  const [port, setPort] = useState(String(data.port));
  const [scanNow, setScanNow] = useState(false);
  const [rowErrors, setRowErrors] = useState<string[]>([]);
  const [portError, setPortError] = useState('');
  const [failure, setFailure] = useState('');
  const [saved, setSaved] = useState<SaveResult | null>(null);
  const [focusRow, setFocusRow] = useState<number | null>(null);
  const busy = useRef(false);
  const revision = useRef(data.revision);
  const rows = useRef<(HTMLInputElement | null)[]>([]);
  const saveButton = useRef<HTMLButtonElement>(null);

  // 新加的一行直接接过焦点：添加之后下一步一定是往里打路径。布局效应在提交 DOM 后立刻跑，焦点不等下一帧。
  useLayoutEffect(() => {
    if (focusRow === null) return;
    rows.current[focusRow]?.focus();
    setFocusRow(null);
  }, [focusRow]);

  useEffect(() => {
    if (!saved) return undefined;
    const timer = setTimeout(() => location.assign(saved.url), RESTART_REDIRECT_MS);
    return () => clearTimeout(timer);
  }, [saved]);

  const update = (index: number, value: string) => {
    setDirs((list) => list.map((dir, i) => (i === index ? value : dir)));
  };
  const add = () => {
    setFocusRow(dirs.length);
    setDirs((list) => [...list, '']);
  };
  const remove = (index: number) => {
    setKinds((list) => list.filter((_, i) => i !== index));
    setRoots((list) => list.filter((_, i) => i !== index));
    setDirs((list) => list.filter((_, i) => i !== index));
    setRowErrors((errors) => errors.filter((_, i) => i !== index));
  };
  const setRowError = (index: number, message: string) => {
    setRowErrors((errors) => {
      const next = [...errors];
      while (next.length <= index) next.push('');
      next[index] = message;
      return next;
    });
  };
  // 对话框开着的时候按钮置忙；取消什么也不改，打不开时原因写在这一行下面。
  const pick = async (index: number, button: HTMLButtonElement) => {
    if (button.getAttribute('aria-busy') === 'true') return;
    setActionBusy(button, true);
    try {
      const { path } = await apiSend<{ path: string | null }>(PICK_FOLDER_URL, { initial: dirs[index] ?? '' });
      if (path) {
        update(index, path);
        setRowError(index, '');
      }
    } catch (cause) {
      setRowError(index, errorMessage(cause));
    } finally {
      setActionBusy(button, false);
    }
  };

  const submit = async (event: JSX.TargetedEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy.current) return;
    busy.current = true;
    setActionBusy(saveButton.current, true);
    setFailure('');
    try {
      const result = await apiSend<SaveResult>(CONFIGURATION_URL, {
        revision: revision.current,
        media_dirs: dirs,
        ...(data.media_sources ? { media_sources: dirs.map((path, i) => ({ path, location: kinds[i] || 'local', root: roots[i] || '' })) } : {}),
        port,
        scan_now: scanNow,
      });
      revision.current = result.revision;
      setRowErrors([]);
      setPortError('');
      receipt('已保存配置');
      setSaved(result);
    } catch (cause) {
      const fields = fieldErrorsOf(cause);
      if (fields) {
        setRowErrors(fields.media_dirs ?? []);
        setPortError(fields.port ?? '');
      } else {
        setRowErrors([]);
        setPortError('');
        setFailure(errorMessage(cause));
      }
    } finally {
      busy.current = false;
      setActionBusy(saveButton.current, false);
    }
  };

  if (saved) {
    return (
      <div class="configsaved" role="status">
        <Html html={noteHtml('配置已保存，Peach 正在重新启动。', { variant: 'success', label: '已保存' })} />
        <p class="confighelp">
          几秒后自动打开新地址；没跳转就点 <a href={saved.url}>进入馆藏</a>。
        </p>
      </div>
    );
  }

  return (
    <form class="configfieldset" data-geist-fieldset aria-labelledby="configTitle" onSubmit={submit} noValidate>
      <div class="geist-fieldset-content">
        <Html html={fieldsetTitle('configTitle', '这台电脑')} />
        <div class="configfield">
          <span class="configlabel" id="configDirsLabel">媒体文件夹</span>
          <div class="configdirs" role="group" aria-labelledby="configDirsLabel">
            {dirs.map((value, index) => (
              <div class="configdir" key={index}>
                <span class="configpathlabel">本机文件夹 {index + 1}</span>
                <input
                  class="geist-input"
                  type="text"
                  value={value}
                  aria-label={`媒体文件夹 ${index + 1}`}
                  aria-invalid={rowErrors[index] ? 'true' : undefined}
                  onInput={(event) => update(index, event.currentTarget.value)}
                  ref={(el) => { rows.current[index] = el; }}
                />
                <button type="button" class="geist-button configpick" aria-label="选择文件夹" onClick={(event) => pick(index, event.currentTarget)}>
                  <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-folder-search" /></svg>
                </button>
                {dirs.length > 1 ? (
                  <button type="button" class="geist-button configrm" aria-label="移除这个文件夹" onClick={() => remove(index)}>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-x" /></svg>
                  </button>
                ) : null}
                <div class="configsource">
                  <div class="configsourcelabel">媒体来源
                    <MediaSourceSelect label={`媒体来源 ${index + 1}`} value={kinds[index] || 'local'}
                      onChange={(value) => { const next = [...kinds]; next[index] = value; setKinds(next); }} />
                  </div>
                  {data.windows === false ? <label>Windows 中的对应路径
                    <input class="geist-input" aria-label={`Windows 中的对应路径 ${index + 1}`} value={roots[index] || ''} placeholder="例如 B:\\"
                      onInput={(event) => { const next = [...roots]; next[index] = event.currentTarget.value; setRoots(next); }} />
                  </label> : null}
                </div>
                {rowErrors[index] ? <p class="configbad" role="alert">{rowErrors[index]}</p> : null}
              </div>
            ))}
          </div>
          <button type="button" class="geist-button configadd" onClick={add}>添加文件夹</button>
          {kinds.some((kind) => kind === '115' || kind === 'pikpak') ? <p class="confighelp">先在 CloudDrive 登录网盘并完成挂载。<a href="https://www.clouddrive2.com/help.html" target="_blank" rel="noreferrer">挂载帮助<svg aria-hidden="true" viewBox="0 0 24 24"><use href="#i-external-link" /></svg></a></p> : null}
          {data.windows === false ? <p class="confighelp">本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\ 对应本机挂载文件夹。</p> : null}
        </div>
        <div class="configfield">
          <label for="configPort">本机访问端口</label>
          <input
            id="configPort"
            class="geist-input"
            type="text"
            inputMode="numeric"
            value={port}
            aria-invalid={portError ? 'true' : undefined}
            onInput={(event) => setPort(event.currentTarget.value)}
          />
          {portError ? <p class="configbad" role="alert">{portError}</p> : null}
          <p class="confighelp">浏览器地址里冒号后面的数字，一般不用改。</p>
        </div>
        <label class="configcheck">
          <span class="pcheck">
            <input type="checkbox" checked={scanNow} onChange={(event) => setScanNow(event.currentTarget.checked)} />
            <span aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-check" /></svg></span>
          </span>
          <span>保存后扫描媒体文件夹</span>
        </label>
        {failure ? <Html html={noteHtml(failure, { variant: 'error', label: '没有保存' })} /> : null}
      </div>
      <div class="geist-fieldset-footer" data-geist-fieldset-footer>
        <p>保存后 Peach 会重新启动，端口改了就用新地址打开。</p>
        <button type="submit" class="geist-button primary" ref={saveButton}>保存配置</button>
      </div>
    </form>
  );
}

export function Configuration({ receipt, data, error }: ConfigurationProps & State) {
  if (error || !data) {
    return <Html class="configpage" html={noteHtml(error || '没有读到配置', { variant: 'error', label: '打不开配置' })} />;
  }
  return (
    <div class="configpage">
      {data.editable
        ? <ConfigurationForm data={data} receipt={receipt} />
        : <Html html={noteHtml(data.notice, { variant: 'secondary', label: '只读' })} />}
      <Facts facts={data.facts} />
      <MountStatus data={data} />
    </div>
  );
}
