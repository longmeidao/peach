/* 来源和凭证页：每个采集来源怎么连、拿什么身份连，外加一趟按番号补高清封面。
 *
 * 这是第一个带写操作的 React 档，两件事在这里定型：
 * - **写操作是 `useMutation`**，不进 Query 的缓存节律。保存成功后用 `setQueryData` 把服务端
 *   回的那一条换进列表，而不是把整页重取一遍：用户可能正在填另一张卡，重取会把它一起重画。
 *   失败只在卡内留一句原因，缓存里的上一份数据不动。
 * - **后台任务是按状态开关的 `refetchInterval`**：跑起来两秒一次，停了就不问。轮询跟着组件走，
 *   遗留壳换页时卸根，它自己就停了。
 *
 * 还有一条只在有后台任务的页面才成立：**首屏读到的旧结果不冒充新结果**。抓封面关掉页面
 * 照样在跑，所以任务状态里常年躺着上一趟的回执；它是那一刻的快照，铺开会被读成刚刚跑完。
 * 只有本次启动过、或者本次亲眼见过它在跑，终态才画成结果并发回执。 */
import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { RiArrowRightLine } from '@remixicon/react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Radio, RadioGroup } from 'react-aria-components';
import { siteMarkUrl } from '@peach/legacy/core';

import { SettingsRow } from '@/components/application/settings/settings-rows';
import { Button } from '@/components/base/buttons/button';
import { LinkButton } from '@/components/base/buttons/link-button';
import { Input } from '@/components/base/input/input';
import { Select, SelectItem } from '@/components/base/select/select';

import { apiSend, errorMessage } from '../../api';
import type { ScrapingProps } from '../bundle';
import { LoadingDots } from '../components/loading-dots';
import { Note } from '../components/note';
import { Page } from '../components/page';
import { queryClient } from '../query';
import {
  ErrorText, ExternalLink, FieldLabel, Footer, Rows, Section, Stack,
} from '../settings/section';
import { busyProps } from '../settings/use-action';
import {
  checkText, COOKIE_TEXT_LIMIT, COVER_JOB_KEY, COVER_POLL_MS, fetchCoverJob, fetchSources,
  SCRAPING_CHECK_URL, SCRAPING_COVER_URL, SCRAPING_KEY, SCRAPING_SETTINGS_URL,
  type Check, type CoverJob, type ScrapingData, type Source,
} from './scraping';

const NETWORKS = [['peach', 'Peach 代理'], ['direct', '直接连接']] as const;
const COOKIE_METHODS = [['paste', '粘贴 Cookie'], ['file', '导入文件']] as const;

/* 前面是站点自己的图标（指对象），后面是外链箭头（指形态）——两枚都在
   `vercel-geist-button-icons.md` 的「加图标」那一侧，中间的地址不重复说这两件事。
   图标走服务端的 `/site-mark`：这一页确实本来就要连这些站，但浏览器直连只拿得到
   `/favicon.ico` 那一枚 16px，站点自己备好的 apple-touch-icon 和 SVG 问都不问；
   需要代理才通的来源更是常年空着。取不到时把 `<img>` 摘掉，不留破图。 */
function SiteMark({ source }: { source: string }) {
  return (
    <img src={siteMarkUrl({ source })} alt="" width={16} height={16} loading="lazy"
      onError={(event) => event.currentTarget.remove()}
      className="size-4 shrink-0 rounded-sm object-contain" />
  );
}

/** 一个来源一张卡：怎么连、拿什么身份连，底下三个动作。 */
function SourceCard({ source, toast }: { source: Source } & ScrapingProps) {
  const [network, setNetwork] = useState(source.network);
  const [cookie, setCookie] = useState('');
  const [cookieText, setCookieText] = useState('');
  const [method, setMethod] = useState<string>(COOKIE_METHODS[0][0]);
  const [fileName, setFileName] = useState('');
  const [fileProblem, setFileProblem] = useState('');
  const file = useRef<HTMLInputElement>(null);

  /* 秘密只在提交那一刻存在于页面上：保存回来之后输入框清空，页面上不再留着刚交上去的
     那一份。文件选择器自己也要清，否则同名文件再选一次不会触发 change。 */
  function forgetSecrets() {
    setCookie('');
    setCookieText('');
    setFileName('');
    setFileProblem('');
    if (file.current) file.current.value = '';
  }

  const save = useMutation({
    mutationFn: (revoke: boolean) => apiSend<{ saved: Source }>(SCRAPING_SETTINGS_URL, {
      source: source.source, network, cookie, cookies_text: cookieText, revoke,
    }),
    onSuccess: (result, revoke) => {
      // 服务端回的就是这一条的新样子，换进列表即可，不为一次保存把整页重取一遍。
      queryClient.setQueryData<ScrapingData>(SCRAPING_KEY, (current) => current && {
        ...current,
        sources: current.sources.map(
          (row) => (row.source === result.saved.source ? result.saved : row)),
      });
      forgetSecrets();
      toast(revoke ? 'Cookie 已撤销' : '来源设置已保存');
    },
  });
  const check = useMutation({
    mutationFn: () => apiSend<{ results: Check[] }>(SCRAPING_CHECK_URL, { source: source.source }),
  });
  // 一张卡上三个动作互斥：它们改的是同一份凭据，谁先落地都会让另一次的结果说不清楚。
  const busy = save.isPending || check.isPending;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy) return;
    check.reset();
    save.mutate(false);
  };
  const revoke = () => {
    if (busy) return;
    check.reset();
    save.mutate(true);
  };
  const connect = () => {
    if (busy) return;
    save.reset();
    check.mutate();
  };

  async function pickFile(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const selected = input.files?.[0];
    setCookieText('');
    setFileProblem('');
    if (!selected) {
      setFileName('');
      return;
    }
    if (selected.size > COOKIE_TEXT_LIMIT) {
      // 超限的多半根本不是 Cookie 文件。在浏览器里就拦住，不拿它去占一次请求。
      input.value = '';
      setFileName('');
      setFileProblem('Cookie 文本超过 256 KiB');
      return;
    }
    try {
      const text = await selected.text();
      setCookieText(text);
      setFileName(selected.name);
    } catch {
      setFileProblem('Cookie 文件未读取，请重新选择');
    }
  }

  const problem = fileProblem
    || (save.error ? errorMessage(save.error) : '')
    || (check.error ? errorMessage(check.error) : '');
  const results = check.data?.results ?? [];
  // 这一块空着时连同它那道分隔线一起不画：直连、又不收 Cookie 的来源只有一行连接方式。
  const detailed = network === 'peach' || source.accepts_cookie || !!problem || results.length > 0;

  return (
    <Section title={source.label} onSubmit={submit} aside={
      <span className="flex min-w-0 items-center gap-1">
        <SiteMark source={source.source} />
        <ExternalLink href={source.login}>{source.login}</ExternalLink>
      </span>
    }>
      <Rows>
        <SettingsRow label="连接方式">
          <Select aria-label="连接方式" selectedKey={network}
            onSelectionChange={(key) => { if (key !== null) setNetwork(String(key)) }}>
            {NETWORKS.map(([key, name]) => <SelectItem key={key} id={key}>{name}</SelectItem>)}
          </Select>
        </SettingsRow>
      </Rows>
      {detailed ? <Stack divided>
        {network === 'peach'
          ? <span className="self-start">
              <LinkButton href="/configuration#peachProxy" size="small" trailingIcon={RiArrowRightLine}>
                配置 Peach 代理
              </LinkButton>
            </span>
          : null}
        {source.accepts_cookie ? <>
          <p className="text-body-2-regular text-text-secondary">
            {source.cookie_saved
              ? 'Cookie 已保存，登录是否有效请在抓取时确认。'
              : '需要登录时，任选一种方式提供 Cookie。'}
          </p>
          {/* 两种方式互斥，交上去的只能是其中一种：切换时把另一种的输入清掉，
              不让看不见的那一份跟着提交。 */}
          <RadioGroup aria-label="提供 Cookie 的方式（二选一）" value={method}
            onChange={(next) => { setMethod(next); forgetSecrets() }}
            className="flex flex-wrap gap-1">
            {COOKIE_METHODS.map(([value, label]) => (
              <Radio key={value} value={value}
                className="flex h-8 cursor-pointer items-center rounded-lg px-3 text-body-2-medium text-text-secondary outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring data-selected:bg-background-tertiary-default data-selected:text-text-primary">
                {label}
              </Radio>
            ))}
          </RadioGroup>
          {method === 'paste'
            ? <Input type="password" label="Cookie" autoComplete="off" value={cookie} onChange={setCookie} />
            : <div className="flex flex-col gap-2">
                <FieldLabel>Netscape Cookie 文件（.txt）</FieldLabel>
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="secondary" onClick={() => file.current?.click()}>选择文件</Button>
                  <span className="min-w-0 text-body-2-regular break-all text-text-secondary">
                    {fileName || '未选择文件'}
                  </span>
                </div>
                {/* 原生文件选择器长相不可控，按钮归 BoardUI，输入框只留着接文件。 */}
                <input ref={file} type="file" accept=".txt" tabIndex={-1} aria-hidden
                  className="hidden" onChange={(event) => { void pickFile(event) }} />
              </div>}
        </> : null}
        {problem ? <ErrorText>{problem}</ErrorText> : null}
        {results.map((result) => (
          <Note key={result.label} tone={result.ok ? 'success' : 'error'}>
            {checkText(result, source.label)}
          </Note>
        ))}
      </Stack> : null}
      {/* 主体动作在最右。次级动作先出现，`保存` 是这张卡唯一的写入，放在一行的末尾；
          表单里只有它一个 `type=submit`，所以挪位置不影响回车提交。 */}
      <Footer>
        {source.accepts_cookie && source.cookie_saved
          ? <Button variant="secondary" onClick={revoke} {...busyProps(busy)}>撤销 Cookie</Button>
          : null}
        <Button variant="secondary" onClick={connect} {...busyProps(busy)}>检查连接</Button>
        <Button type="submit" {...busyProps(busy)}>保存</Button>
      </Footer>
    </Section>
  );
}

/** 按番号补一张高清封面。这一趟在后台跑，页面上留状态。 */
function CoverCard({ toast }: ScrapingProps) {
  const [code, setCode] = useState('');
  /** 本次是不是在跟一趟：启动过，或者本次见过它在跑。 */
  const [tracking, setTracking] = useState(false);
  /** 本次跟完的那一趟。首屏读到的旧终态不算，它不会走到这里。 */
  const [outcome, setOutcome] = useState<CoverJob | null>(null);

  const job = useQuery({
    queryKey: COVER_JOB_KEY,
    queryFn: ({ signal }) => fetchCoverJob(signal),
    refetchInterval: (query) => (query.state.data?.status === 'running' ? COVER_POLL_MS : false),
  });
  const start = useMutation({
    mutationFn: () => apiSend<CoverJob>(SCRAPING_COVER_URL, { code }),
    onSuccess: () => {
      setTracking(true);
      setOutcome(null);
      // 启动的那一次回的就是任务快照，但轮询的节律由这个键说了算：让它立刻重读一次接上。
      void queryClient.invalidateQueries({ queryKey: COVER_JOB_KEY });
    },
  });

  const status = job.data?.status ?? 'idle';
  const running = status === 'running';
  useEffect(() => {
    const state = job.data;
    if (!state) return;
    if (state.status === 'running') {
      if (!tracking) setTracking(true);
      return;
    }
    if (!tracking) return;
    setTracking(false);
    setOutcome(state);
    if (state.status === 'complete') toast(state.result || '封面采集完成');
  }, [job.data, tracking, toast]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (running || start.isPending || !code.trim()) return;
    start.mutate();
  };

  const problem = start.error ? errorMessage(start.error)
    : outcome?.status === 'failed' ? (outcome.error || '采集未取得') : '';
  return (
    <Section title="高清封面" onSubmit={submit}>
      <Stack>
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-0 flex-1">
            <Input aria-label="馆藏番号" isRequired isDisabled={running} value={code} onChange={setCode}
              placeholder="输入馆藏番号，如 ABW-232" />
          </div>
          <Button type="submit" disabled={!code.trim()} {...busyProps(running || start.isPending)}>
            抓取封面
          </Button>
        </div>
        {/* 这一趟要挨个问几家站点、还可能走代理，没有可数的总量，也不能编一个百分比出来。
            关掉页面它照样在跑，回来能接上，所以状态得留在页面上，而不是只让按钮转一下。 */}
        {running ? <LoadingDots label="正在抓取封面" /> : null}
        {problem ? <Note tone="error">{problem}</Note> : null}
        {outcome?.status === 'complete'
          ? <Note tone="success">{outcome.result || '封面采集完成'}</Note>
          : null}
      </Stack>
    </Section>
  );
}

export function ScrapingPage({ toast }: ScrapingProps) {
  const sources = useQuery({ queryKey: SCRAPING_KEY, queryFn: ({ signal }) => fetchSources(signal) });
  const data = sources.data;
  if (!data) {
    return (
      <Page>
        <Note tone="error" title="读取失败">
          {sources.error ? errorMessage(sources.error) : '读取采集来源失败'}
        </Note>
      </Page>
    );
  }
  return (
    <Page>
      <p className="text-body-2-regular text-text-secondary">高清图片可能需要代理才能下载，请先检查连接。</p>
      <CoverCard toast={toast} />
      {(data.sources || []).map(
        (source) => <SourceCard key={source.source} source={source} toast={toast} />)}
    </Page>
  );
}
