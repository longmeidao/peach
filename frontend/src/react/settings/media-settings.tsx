/* 「媒体」分组：这台电脑的媒体文件夹与本机端口，加各来源的挂载状态。
 *
 * 服务端按两道门放行：托盘管理的服务、且从运行 Peach 的这台电脑打开时 `editable` 才为真；
 * 其它情况表单不画，只留一句为什么。保存成功后 Peach 会重启，这里给一句持久提示、一条新地址
 * 的链接，并在托盘换好进程后自己跳过去。
 *
 * 校验原因由服务端按字段给（400 的 `errors`），页面写回原位，不在前端复制一份路径与端口的判定。 */
import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from 'react';
import { RiCloseLine } from '@remixicon/react';
import { MEDIA_SOURCE_ICONS } from '@peach/legacy/ui';

import { Button } from '@/components/base/buttons/button';
import { IconButton } from '@/components/base/buttons/icon-button';
import { LinkButton } from '@/components/base/buttons/link-button';
import { Checkbox } from '@/components/base/checkbox/checkbox';
import { Input } from '@/components/base/input/input';
import { Select, SelectItem } from '@/components/base/select/select';

import { ApiError, apiGet, apiSend, errorMessage } from '../../api';
import { CONFIGURATION_URL, PICK_FOLDER_URL } from '../../configuration-endpoints';
import type { ConfigurationData, ConfigurationGroupProps } from '../bundle';
import { CloudDriveGuide } from './clouddrive-guide';
import { LibraryIconPicker } from './library-icon-picker';
import {
  ErrorText, ExternalLink, Fact, FactList, FieldLabel, Footer, Help, Note, Section, SourceMark, Stack,
} from './section';
import { busyProps, useAction } from './use-action';

/** 保存后等托盘换好进程再跳到新地址的时间。首启完成页用的是同一个数。 */
export const RESTART_REDIRECT_MS = 8000;

/** 「选择文件夹」弹系统对话框去挑，全站用雪碧图的 `folder-search`；`folder-open` 归「打开位置」，
 * Remix Icon 里没有这一枚。 */
function FolderSearchIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
      strokeLinecap="round" strokeLinejoin="round" className={className}>
      <use href="#i-folder-search" />
    </svg>
  );
}

export const MEDIA_SOURCES = [['local', '本地磁盘'], ['115', 'CloudDrive · 115'], ['pikpak', 'CloudDrive · PikPak']] as const;

const sourceName = (location: string) => MEDIA_SOURCES.find(([kind]) => kind === location)?.[1] ?? location;
const sourceMark = (location: string) => MEDIA_SOURCE_ICONS[location] || 'database';

interface FolderRow { path: string; location: string; root: string; library: string; library_icon: string }
interface FieldErrors { media_dirs?: string[]; port?: string }
interface SaveResult { saved: boolean; url: string; revision: string }

const blankRow = (path = ''): FolderRow => ({ path, location: 'local', root: '', library: '', library_icon: '' });

function initialRows(data: ConfigurationData): FolderRow[] {
  const known = data.media_sources?.filter((row) => MEDIA_SOURCES.some(([kind]) => kind === row.location));
  if (known?.length) {
    return known.map((row) => ({
      path: row.path, location: row.location, root: row.root, library: row.library || '', library_icon: row.library_icon || '',
    }));
  }
  return (data.media_dirs.length ? data.media_dirs : ['']).map((path) => blankRow(path));
}

const fieldErrorsOf = (cause: unknown): FieldErrors | null => {
  if (!(cause instanceof ApiError) || cause.status !== 400) return null;
  return (cause.body as { errors?: FieldErrors } | null)?.errors ?? null;
};

export function MediaSettings({ data, receipt }: ConfigurationGroupProps) {
  return (
    <div className="flex flex-col gap-6">
      {data.editable ? <MediaForm data={data} receipt={receipt} /> : <Note tone="neutral" title="只读">{data.notice}</Note>}
      <MountStatus data={data} />
    </div>
  );
}

function MediaForm({ data, receipt }: ConfigurationGroupProps) {
  const [rows, setRows] = useState(() => initialRows(data));
  const [port, setPort] = useState(String(data.port));
  const [scanNow, setScanNow] = useState(false);
  const [rowErrors, setRowErrors] = useState<string[]>([]);
  const [portError, setPortError] = useState('');
  const [failure, setFailure] = useState('');
  const [saved, setSaved] = useState<SaveResult | null>(null);
  const [focusRow, setFocusRow] = useState<number | null>(null);
  const [picking, setPicking] = useState<number | null>(null);
  const pickingNow = useRef(false);
  const revision = useRef(data.revision);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);
  const action = useAction();

  // 新加的一行直接接过焦点：添加之后下一步一定是往里打路径。
  useLayoutEffect(() => {
    if (focusRow === null) return;
    inputs.current[focusRow]?.focus();
    setFocusRow(null);
  }, [focusRow]);

  useEffect(() => {
    if (!saved) return undefined;
    const timer = setTimeout(() => location.assign(saved.url), RESTART_REDIRECT_MS);
    return () => clearTimeout(timer);
  }, [saved]);

  const edit = (index: number, patch: Partial<FolderRow>) =>
    setRows((list) => list.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  const setRowError = (index: number, message: string) => setRowErrors((errors) => {
    const next = [...errors];
    while (next.length <= index) next.push('');
    next[index] = message;
    return next;
  });
  const add = () => {
    setFocusRow(rows.length);
    setRows((list) => [...list, blankRow()]);
  };
  const remove = (index: number) => {
    setRows((list) => list.filter((_, i) => i !== index));
    setRowErrors((errors) => errors.filter((_, i) => i !== index));
  };

  // 对话框开着的时候这一行的选择键置忙；取消什么也不改，打不开时原因写在这一行下面。
  const pick = async (index: number) => {
    if (pickingNow.current) return;
    pickingNow.current = true;
    setPicking(index);
    try {
      const { path } = await apiSend<{ path: string | null }>(PICK_FOLDER_URL, { initial: rows[index]?.path ?? '' });
      if (path) {
        edit(index, { path });
        setRowError(index, '');
      }
    } catch (cause) {
      setRowError(index, errorMessage(cause));
    } finally {
      pickingNow.current = false;
      setPicking(null);
    }
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFailure('');
    void action.run('save', (signal) => apiSend<SaveResult>(CONFIGURATION_URL, {
      revision: revision.current,
      media_dirs: rows.map((row) => row.path),
      ...(data.media_sources ? { media_sources: rows } : {}),
      port,
      scan_now: scanNow,
    }, 'POST', signal), (result) => {
      revision.current = result.revision;
      setRowErrors([]);
      setPortError('');
      receipt('已保存配置');
      setSaved(result);
    }, (cause) => {
      const fields = fieldErrorsOf(cause);
      setRowErrors(fields?.media_dirs ?? []);
      setPortError(fields?.port ?? '');
      if (!fields) setFailure(errorMessage(cause));
    });
  };

  if (saved) {
    return (
      <Section title="这台电脑">
        <Stack>
          <Note tone="success" title="配置已保存">
            Peach 正在重新启动。稍后自动跳转，或点击<LinkButton href={saved.url} size="small">进入馆藏</LinkButton>。
          </Note>
        </Stack>
      </Section>
    );
  }

  const cloud = rows.some((row) => row.location === '115' || row.location === 'pikpak');
  const missing = cloud ? (data.mount_dependencies ?? []).filter((dependency) => !dependency.available) : [];
  return (
    <Section title="这台电脑" onSubmit={submit}>
      <Stack>
        <div className="flex flex-col gap-3">
          <FieldLabel>媒体文件夹</FieldLabel>
          <div role="group" aria-label="媒体文件夹" className="flex flex-col gap-3">
            {rows.map((row, index) => (
              <div key={index} data-folder-row className="@container flex flex-col gap-3 rounded-2lg border border-separator-border p-3">
                <div className="flex items-start gap-2">
                  <Input className="min-w-0 flex-1" aria-label={`媒体文件夹 ${index + 1}`} placeholder="本机文件夹路径"
                    value={row.path} onChange={(path) => edit(index, { path })}
                    ref={(el) => { inputs.current[index] = el; }}
                    validationBehavior="aria" isInvalid={Boolean(rowErrors[index])} hint={rowErrors[index] || undefined} />
                  <IconButton icon={FolderSearchIcon} aria-label="选择文件夹" onClick={() => void pick(index)}
                    {...busyProps(picking === index)} />
                  {rows.length > 1
                    ? <IconButton icon={RiCloseLine} aria-label="移除这个文件夹" onClick={() => remove(index)} />
                    : null}
                </div>
                <div className="inline-grid grid-cols-1 gap-3 @lg:grid-cols-2">
                  <Input label="媒体库名称" maxLength={80} placeholder="同名文件夹归入同一个媒体库"
                    value={row.library} onChange={(library) => edit(index, { library })} />
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>媒体库图标</FieldLabel>
                    <LibraryIconPicker label={`媒体库图标 ${index + 1}`} value={row.library_icon} kind={row.location}
                      onChange={(library_icon) => edit(index, { library_icon })} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>媒体来源</FieldLabel>
                    <Select aria-label={`媒体来源 ${index + 1}`} selectedKey={row.location}
                      onSelectionChange={(key) => { if (key !== null) edit(index, { location: String(key) }); }}>
                      {MEDIA_SOURCES.map(([kind, name]) => (
                        <SelectItem key={kind} id={kind} textValue={name}><SourceMark mark={sourceMark(kind)} />{name}</SelectItem>
                      ))}
                    </Select>
                  </div>
                  {data.windows === false
                    ? <Input label="Windows 中的对应路径" placeholder={'例如 B:\\'} value={row.root}
                        onChange={(root) => edit(index, { root })} />
                    : null}
                </div>
              </div>
            ))}
          </div>
          <Button variant="secondary" className="self-start" onClick={add}>添加文件夹</Button>
        </div>
        {cloud ? <CloudDriveGuide /> : null}
        {missing.map((dependency) => (
          <Help key={dependency.name}>
            未检测到 {dependency.name}。<ExternalLink href={dependency.download_url}>下载 {dependency.name}</ExternalLink>
          </Help>
        ))}
        {data.windows === false
          ? <Help>本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\ 对应本机挂载文件夹。</Help>
          : null}
        {data.port_editable !== false
          ? <Input id="configPort" label="本机访问端口" inputMode="numeric" value={port} onChange={setPort}
              validationBehavior="aria" isInvalid={Boolean(portError)} hint={portError || '浏览器地址里冒号后面的数字，一般不用改。'} />
          : null}
        <Checkbox isSelected={scanNow} onChange={setScanNow}>保存后扫描并补全资料</Checkbox>
        {failure ? <Note tone="error" title="没有保存">{failure}</Note> : null}
      </Stack>
      <Footer status={data.port_editable === false ? '保存后 Peach 会重新载入配置。' : '保存后 Peach 会重新启动，端口改了就用新地址打开。'}>
        <Button type="submit" {...busyProps(action.busy === 'save')}>保存配置</Button>
      </Footer>
    </Section>
  );
}

function MountBadge({ online }: { online: boolean | undefined }) {
  if (online === true) {
    return <span data-mount="online" className="inline-flex items-center gap-1.5 text-body-2-medium text-notification-success-foreground"><span aria-hidden className="size-1.5 rounded-full bg-current" />在线</span>;
  }
  if (online === false) {
    return <span data-mount="offline" className="inline-flex items-center gap-1.5 text-body-2-medium text-text-error-primary"><span aria-hidden className="size-1.5 rounded-full bg-current" />离线</span>;
  }
  return <span data-mount="unknown" className="inline-flex items-center gap-1.5 text-body-2-medium text-text-secondary"><span aria-hidden className="size-1.5 rounded-full bg-current" />未检测</span>;
}

function MountStatus({ data }: { data: ConfigurationData }) {
  const [sources, setSources] = useState(data.media_sources);
  const action = useAction();
  if (!sources) return null;
  const refresh = () => void action.run('refresh', (signal) => apiGet<ConfigurationData>(CONFIGURATION_URL, signal),
    (result) => setSources(result.media_sources));
  return (
    <Section title="挂载状态">
      <FactList>
        {sources.map((row, index) => (
          <Fact key={index} term={<><SourceMark mark={sourceMark(row.location)} />{sourceName(row.location)}</>}>
            {row.path || '未配置挂载点'}<MountBadge online={row.online} />
          </Fact>
        ))}
      </FactList>
      {action.error ? <Stack divided><ErrorText>{action.error}</ErrorText></Stack> : null}
      <Footer>
        <Button variant="secondary" onClick={refresh} {...busyProps(action.busy === 'refresh')}>刷新挂载状态</Button>
      </Footer>
    </Section>
  );
}
