/* 来源和凭证页的数据契约与折算。四条端点在 `frontend/src` 里都只在这里声明一次
 * （`tests/test_frontend_build.py` 盯着）。
 *
 * 这一页有两个键，因为屏幕上是两个不同节律的真相：来源列表由用户改、改完由写操作把
 * 那一条换进缓存；封面任务是后台自己推进的状态，跑起来时两秒问一次。合成一个键的话，
 * 每一轮轮询都要把整张来源列表重取一遍，用户正在填的那张卡也会跟着重画。 */
import { apiGet } from '../../api';
import { queryClient } from '../query';

export const SCRAPING_URL = '/api/scraping';
export const SCRAPING_SETTINGS_URL = '/api/scraping/settings';
export const SCRAPING_CHECK_URL = '/api/scraping/check';
export const SCRAPING_COVER_URL = '/api/scraping/cover';

/** 来源列表共用这一个键。 */
export const SCRAPING_KEY = ['scraping'] as const;
/** 抓封面那一趟后台任务的状态。 */
export const COVER_JOB_KEY = ['scraping', 'cover'] as const;

/** 一个采集来源。字段以 `q_scraping`（`src/peach/web_scraping.py`）为准。 */
export interface Source {
  source: string;
  label: string;
  login: string;
  accepts_cookie: boolean;
  network: string;
  cookie_saved: boolean;
}

export interface ScrapingData {
  sources: Source[];
}

/** 一次连接检查的一项结果：来源页面，以及部分来源另有的高清图片地址。 */
export interface Check {
  label: string;
  ok: boolean;
  status?: number;
  message?: string;
  width?: number;
  height?: number;
}

/** 抓封面的后台任务快照（`scraping_cover_job`）。`status` 是 `idle|running|complete|failed`。 */
export interface CoverJob {
  status: string;
  job_id?: string;
  result?: string;
  error?: string;
  width?: number;
  height?: number;
}

/** 在跑的时候两秒问一次，和别的后台任务同一个节律；停了就不再问。 */
export const COVER_POLL_MS = 2000;

/** Netscape Cookie 文件的上限。再大的多半不是 Cookie 文件，先拦住再说。 */
export const COOKIE_TEXT_LIMIT = 256 * 1024;

export const fetchSources = (signal?: AbortSignal) => apiGet<ScrapingData>(SCRAPING_URL, signal);
export const fetchCoverJob = (signal?: AbortSignal) => apiGet<CoverJob>(SCRAPING_COVER_URL, signal);

/** 首屏：两个键都取回来才画。
 *
 * 抓封面的状态也算首屏——页面一上来就得知道有没有一趟正在跑，才接得上它的进度。
 * 中止时 `fetchQuery` 把 `AbortError` 抛回给挂载方，它据此放弃这一次。 */
export async function prefetchScraping(signal: AbortSignal): Promise<void> {
  await Promise.all([
    queryClient.fetchQuery({ queryKey: SCRAPING_KEY, queryFn: () => fetchSources(signal) }),
    queryClient.fetchQuery({ queryKey: COVER_JOB_KEY, queryFn: () => fetchCoverJob(signal) }),
  ]);
}

/** 一条检查结果说成一句话：谁、通不通、图有多大、服务端补充了什么。
 *
 * 结果里的 `label` 是这一跳查的是什么；只有一跳时它就是来源页面本身，句子里不必再说一遍。 */
export function checkText(check: Check, sourceLabel: string): string {
  return `${sourceLabel}${check.label === '来源页面' ? '' : ' 高清图片'}`
    + `：${check.ok ? '可连接' : '不能连接'}`
    + (check.width ? ` · ${check.width} × ${check.height}` : '')
    + (check.message ? `。${check.message}` : '');
}
