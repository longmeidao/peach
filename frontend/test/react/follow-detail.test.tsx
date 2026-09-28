/* 关注详情岛：单条取数、侧栏的次序与文案、写操作之后键态怎么变、媒体取不回时退到哪、交给壳与灯箱的是什么。
 *
 * 从列表进出不重取、Video.js 接管岛画的 `<video>`、轮播圆点、恢复带、标签回列表与手机布局要真浏览器，
 * 在 `frontend/e2e/follow-detail.test.ts` 里量；尺寸与色板在 `e2e/design.test.ts`。 */
import { notifyManager, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi, type Mock } from 'vitest';

import {
  collectionCopy, detailTags, followItemKey, tagCategory,
  type FollowDetailActions, type FollowDetailData, type FollowDetailItem, type FollowDetailProps,
} from '../../src/react/follow-detail/follow-detail';
import { FollowDetailPage } from '../../src/react/follow-detail/follow-detail-page';
import { FOLLOW_CREDENTIALS_KEY, type FollowFeedHelpers, type FollowGroup } from '../../src/react/follow-feed/follow-feed';
import { openPhotoLightbox } from '../../src/react/photo-lightbox/photo-lightbox-dialog';
import { queryClient } from '../../src/react/query';
import { click, mount, settle } from './render';

/* 灯箱自己的开合与翻页在 `photo-lightbox.test.tsx`；这里只看详情把哪一组、从第几张交给它。 */
vi.mock('../../src/react/photo-lightbox/photo-lightbox-dialog', () => ({ openPhotoLightbox: vi.fn(async () => {}) }));

afterEach(() => { queryClient.clear() });
notifyManager.setScheduler((notify) => notify());

const item = (id: number, extra: Partial<FollowDetailItem> = {}): FollowDetailItem => ({
  id, title: `更新 ${id}`, status: 'new', provider: 'kemono', provider_label: 'Kemono', source_id: 1,
  published_at: `2026-09-${String(10 + (id % 10)).padStart(2, '0')}T08:00:00Z`, media_kind: 'video', playable: true,
  thumb_url: `/thumb/${id}`, tags: [], media_items: [], ...extra,
});
const group = (primary: FollowDetailItem, extra: Partial<FollowGroup> = {}): FollowGroup =>
  ({ primary, variants: [], duplicates: [], stack: null, ...extra });
const image = (index: number, extra: Record<string, unknown> = {}) => ({
  index, media_kind: 'image', thumb_url: `/thumb/m${index}`, name: `${index}.jpg`, width: 600, height: 800, ...extra,
});

function helpers(patch: Partial<FollowFeedHelpers> = {}): FollowFeedHelpers {
  return {
    sourceIcon: (provider) => `<img alt="${provider}">`, authorAvatar: () => '', authorName: () => '',
    identity: () => ({ author: '作者', avatar: '<span>作</span>', credited: '' }), workMark: () => '', titleMarks: () => '',
    badges: () => '', mediaIssue: () => '', when: (shown) => String(shown.published_at || ''), tagLabel: (tag) => tag,
    wireDrag: vi.fn(), wireScroller: vi.fn(), learnDims: vi.fn(), listSkeletonHtml: () => '', jobProgress: vi.fn(),
    ...patch,
  };
}

type ActionMocks = { [K in keyof FollowDetailActions]: Mock<FollowDetailActions[K]> };

function actions(): ActionMocks {
  return {
    close: vi.fn(), openItem: vi.fn(), openTag: vi.fn(), present: vi.fn(), mountPlayer: vi.fn(() => vi.fn()),
    toast: vi.fn(), failure: vi.fn(),
  };
}

const data = (shown: FollowDetailItem, row: FollowGroup | null = group(shown)): FollowDetailData =>
  ({ item: shown, group: row, sources: [], aliases: [] });

/** 假服务端：凭据为空，写接口按 `status` 回话；单条取数回给定的那一页。 */
function serve({ page = null as unknown, status = 200 } = {}) {
  const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.startsWith('/api/follow/credentials')) return { ok: true, status: 200, json: async () => ({ providers: [] }) };
    if (url.startsWith('/api/follow?item=')) return { ok: true, status: 200, json: async () => structuredClone(page) };
    if (init?.method === 'POST') return { ok: status < 400, status, json: async () => (status < 400 ? { ok: true } : { detail: '写入失败' }) };
    return { ok: false, status: 404, json: async () => ({}) };
  });
  vi.stubGlobal('fetch', fetcher);
  return fetcher;
}
const posts = (fetcher: ReturnType<typeof serve>) => fetcher.mock.calls
  .filter(([, init]) => init?.method === 'POST').map(([url, init]) => [url, JSON.parse(String(init!.body))]);

/** 条目与凭据已在缓存里（从列表点进来的那种），直接画，不发请求。 */
async function show(given: FollowDetailData, patch: Partial<FollowDetailProps> = {}) {
  queryClient.setQueryData(followItemKey(given.item.id), given);
  queryClient.setQueryData(FOLLOW_CREDENTIALS_KEY, { providers: [] });
  const props: FollowDetailProps = {
    id: given.item.id, mediaIndex: null, mediaView: 'videos', helpers: helpers(), actions: actions(), ...patch,
  };
  const host = await mount(<QueryClientProvider client={queryClient}><FollowDetailPage {...props} /></QueryClientProvider>);
  await settle();
  return { host, props, actions: props.actions as ActionMocks };
}

describe('取数', () => {
  it('缓存里没有这一条就单条取 `/api/follow?item=`，取回的组里找不到这一条就报出来', async () => {
    const fetcher = serve({ page: { groups: [group(item(8))], sources: [], author_aliases: [] } });
    const props: FollowDetailProps = { id: 8, mediaIndex: null, mediaView: 'videos', helpers: helpers(), actions: actions() };
    const host = await mount(<QueryClientProvider client={queryClient}><FollowDetailPage {...props} /></QueryClientProvider>);
    await settle();
    expect(fetcher.mock.calls.map(([url]) => url)).toContain('/api/follow?item=8');
    expect(host.querySelector('[data-follow-detail-name]')?.textContent).toBe('更新 8');

    queryClient.clear();
    serve({ page: { groups: [], sources: [], author_aliases: [] } });
    const gone = await mount(<QueryClientProvider client={queryClient}><FollowDetailPage {...props} id={9} /></QueryClientProvider>);
    await vi.waitFor(async () => {
      await settle();
      expect(gone.textContent).toContain('这条关注内容已不存在');
    });
  });
});

describe('侧栏', () => {
  it('自上而下：正文、操作、状态一行、标签；标签按 rule34 的类型顺序', async () => {
    const { host } = await show(data(item(1, {
      summary: '正文', detail_tags: ['solo', 'kou', 'ow', 'animated', 'odd', 'tracer'],
      tag_types: { ow: 'copyright', tracer: 'character', kou: 'artist', solo: 'general', animated: 'metadata' },
    })));
    const [summary, actionsBar, state, tags] = ['[data-follow-detail-summary]', '[data-follow-detail-actions]',
      '[data-follow-state]', '[data-follow-detail-tags]'].map((selector) => host.querySelector(selector)!);
    const follows = (a: Element, b: Element) => !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect([follows(summary!, actionsBar!), follows(actionsBar!, state!), follows(state!, tags!)]).toEqual([true, true, true]);
    expect([...host.querySelectorAll<HTMLElement>('[data-follow-tag]')].map((tag) => [tag.dataset.followTag, tag.dataset.tagCat]))
      .toEqual([['ow', 'r34-copyright'], ['tracer', 'r34-character'], ['kou', 'r34-artist'], ['solo', 'r34-general'],
        ['animated', 'r34-metadata'], ['odd', 'r34-unknown']]);
  });

  it('来源外链、网盘链接与下载键；发布者与署名作者不同才写', async () => {
    const { host } = await show(data(item(2, {
      url: 'https://example.invalid/post/2', author: 'Poster',
      resource_urls: ['https://gofile.io/d/a', 'https://mega.nz/folder/b', 'https://files.example.org/c'],
    })));
    const origin = host.querySelector('[data-follow-origin]')!;
    expect([origin.getAttribute('title'), origin.getAttribute('aria-label'), origin.getAttribute('href')])
      .toEqual(['打开来源页面', '打开来源页面', 'https://example.invalid/post/2']);
    expect([...host.querySelectorAll('[data-follow-resources] a')].map((link) => link.textContent))
      .toEqual(['Gofile', 'MEGA', 'files.example.org']);
    const download = host.querySelector('[data-follow-download]')!;
    expect(download.hasAttribute('download')).toBe(true);
    expect(download.getAttribute('href')).toBe('/follow-stream?id=2&download=1');
    expect(host.querySelector('[data-follow-detail-identity] > div')?.textContent).toBe('作者发布者 Poster');
  });

  it('壳判出的媒体提示原样画在侧栏里', async () => {
    const note = 'F95 的附件要登录后才看得到，去来源页面打开。';
    const { host } = await show(data(item(3, { playable: false, media_kind: 'external' })),
      { helpers: helpers({ mediaIssue: () => note }) });
    expect(host.querySelector('[data-follow-media-issue]:not([hidden])')?.textContent).toBe(note);
  });
});

describe('写操作', () => {
  it('保存：键还在、改说「已保存」；回执不带撤销', async () => {
    const fetcher = serve();
    const { host, actions: given } = await show(data(item(4)));
    await click(host.querySelector('[data-follow-detail-save]'));
    await settle();
    expect(posts(fetcher)).toEqual([['/api/follow/save', { item: 4 }]]);
    const save = host.querySelectorAll('[data-follow-detail-save]');
    expect(save).toHaveLength(1);
    expect(save[0]!.getAttribute('aria-label')).toBe('已保存');
    expect(given.toast).toHaveBeenCalledWith('已保存到账本');
  });

  it('标记已看：键按下、多一枚「恢复未看」；回执的撤销写回原状态', async () => {
    const fetcher = serve();
    const { host, actions: given } = await show(data(item(5)));
    expect(host.querySelector('[data-follow-detail-status="ignored"] use')?.getAttribute('href')).toBe('#i-eye-off');
    expect(host.querySelector('[data-follow-detail-status="new"]')).toBeNull();
    await click(host.querySelector('[data-follow-detail-status="seen"]'));
    await settle();
    expect(host.querySelector('[data-follow-detail-status="seen"]')?.getAttribute('aria-pressed')).toBe('true');
    expect(host.querySelector('[data-follow-detail-status="new"]')).not.toBeNull();
    const [message, options] = given.toast.mock.calls[0]!;
    expect(message).toBe('已标记看过');
    await options!.undo!();
    await settle();
    expect(posts(fetcher)).toEqual([['/api/follow/status', { item: 5, to: 'seen' }], ['/api/follow/status', { item: 5, to: 'new' }]]);
    expect(host.querySelector('[data-follow-detail-status="seen"]')?.getAttribute('aria-pressed')).toBe('false');
  });

  it('写失败：键态不变，原因落在状态那一行，并交壳报错', async () => {
    serve({ status: 500 });
    const { host, actions: given } = await show(data(item(6)));
    await click(host.querySelector('[data-follow-detail-status="ignored"]'));
    await settle();
    expect(host.querySelector('[data-follow-detail-status="ignored"]')?.getAttribute('aria-pressed')).toBe('false');
    expect(host.querySelector('[data-follow-state]')?.textContent).not.toBe('');
    expect(given.failure).toHaveBeenCalledOnce();
  });
});

describe('媒体', () => {
  it('视频交给壳挂播放器，卸下这块媒体区时调回它给的清理', async () => {
    const shown = item(10, { media_items: [{ index: 0, media_kind: 'video' }, image(1)] });
    const { host, actions: given } = await show(data(shown));
    const [video, handed, media] = given.mountPlayer.mock.calls[0]!;
    expect(video).toBe(host.querySelector('video'));
    expect([handed.id, media?.index]).toEqual([10, 0]);
    const release = given.mountPlayer.mock.results[0]!.value;
    await click(host.querySelector('[data-follow-media-item="1"]'));
    expect(release).toHaveBeenCalledOnce();
    expect(host.querySelector('video')).toBeNull();
  });

  it('原图取不回就换上缩略图，并说明这是缩略图', async () => {
    const { host } = await show(data(item(11, {
      media_kind: 'image', thumb_url: '/thumb/11', media_items: [image(0, { thumb_url: '/thumb/11-0' })],
    })));
    const poster = host.querySelector<HTMLImageElement>('[data-follow-detail-poster]')!;
    expect(poster.getAttribute('src')).toBe('/follow-stream?id=11&media=0');
    expect(host.querySelector('[data-media-thumb-fallback]')?.hasAttribute('hidden')).toBe(true);
    poster.dispatchEvent(new Event('error'));
    await settle();
    expect(poster.getAttribute('src')).toBe('/thumb/11-0');
    expect(host.querySelector('[data-media-thumb-fallback]')?.hasAttribute('hidden')).toBe(false);
  });

  it('多图帖点图把整组交给灯箱，从当前这张开始', async () => {
    const shown = item(12, { media_kind: 'image', media_items: [image(0), image(1), image(2)] });
    const { host } = await show(data(shown), { mediaIndex: 1 });
    await click(host.querySelector('[data-follow-detail-poster]'));
    const [start, slides] = vi.mocked(openPhotoLightbox).mock.calls.at(-1)!;
    expect(start).toBe(1);
    expect(slides.map((slide) => slide.src)).toEqual([0, 1, 2].map((index) => `/follow-stream?id=12&media=${index}`));
  });

  it('多媒体队列按网盘分组，名字走中段省略；合集队列只列可播视频、新到旧', async () => {
    const shown = item(13, { media_items: [
      { index: 0, media_kind: 'video', name: ' a.mp4 ', resource_group: 'g1', resource_group_label: 'Gofile 文件夹' },
      { ...image(1), resource_group: 'g1', resource_group_label: 'Gofile 文件夹' },
    ] });
    const { host } = await show(data(shown));
    expect(host.querySelector('.mixgrouplabel')?.textContent).toBe('Gofile 文件夹 2');
    expect([...host.querySelectorAll('[data-follow-media-item] [data-middle-truncate]')].map((name) => name.textContent))
      .toEqual(['a.mp4', '1.jpg']);

    queryClient.clear();
    const primary = item(20, { published_at: '2026-09-18T00:00:00Z' });
    const row = group(primary, {
      variants: [item(21, { published_at: '2026-09-20T00:00:00Z' }), item(22, { media_kind: 'image' }),
        item(23, { playable: false })],
      duplicates: [item(24, { published_at: '2026-09-19T00:00:00Z' })],
    });
    const { host: collection } = await show(data(primary, row));
    expect([...collection.querySelectorAll<HTMLElement>('[data-follow-queue-item]')].map((line) => Number(line.dataset.followQueueItem)))
      .toEqual([21, 24, 20]);
  });
});

describe('文案与排序', () => {
  it('合集行首：发布串不拿发布时间当版本标签，正文带上作者', () => {
    const reply = item(30, { author: 'kou', summary: '第二段更新', variant_kind: '', published_at: '2026-09-18T00:00:00Z' });
    expect(collectionCopy(group(item(29), { is_release: true }), reply)).toEqual({ label: '视频', title: 'kou：第二段更新' });
    expect(collectionCopy(group(item(29)), item(31, { variant_kind: 'wip' }))).toEqual({ label: 'WIP', title: '更新 31' });
  });

  it('来源站多出来的类型按 general 着色、排在已知类型之后', () => {
    const shown = item(32, { detail_tags: ['b', 'a', 'x'], tag_types: { a: 'general', b: 'general', x: 'lore' } });
    expect(detailTags(shown, (tag) => tag)).toEqual(['a', 'b', 'x']);
    expect(tagCategory(shown, 'x')).toBe('r34-general');
  });
});
