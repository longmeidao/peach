/* 实体资料页顶上那块资料卡，连同资料卡下面、作品上面那一行未入库的新作。
 *
 * 资料卡按 Board 的 profile 卡排：一块 secondary 底、18px 圆角的卡，正文是头像加身份三行
 * （名字、别名与归属、外链），女优有资料时右边再加一栏资料表，同台艺人收进卡底那条色阶带——
 * 那是这个人的附注，不是这一页的正文。卡外面的交集条、筛选条与内容区仍归壳。
 *
 * 头像、同台艺人的脸和新作卡仍由遗留层拼：取图失败时兜底链（`image-fallback.js`）会把 `<img>`
 * 从 DOM 里摘掉、人脸放大（`avatarFrame`）往图上写内联尺寸、等待微光挂在图的父元素上，这几样
 * 都直接改节点，所以那几格用 `dangerouslySetInnerHTML`，React 不拥有里面的节点。 */
import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { entityPath, esc, icon } from '@peach/legacy/core';

import { AvatarPicker } from '../avatar-picker/avatar-picker-page';
import { FeedNewRow } from '../feed-new/feed-new-row';
import { Glyph } from './glyph';
import { FeedSwitch, MorePop } from './hero-pop';
import { NamePicker } from './name-picker';
import {
  agencyOf, entityFeedTip, entryMarks, factRows, heroLinks, isCompany, isPeople, nameChoices, nameLine, shownTags,
  type EntityHeroActions, type EntityHeroData, type EntityHeroHelpers, type EntityHeroProps,
  type LinkMark, type LinkView,
} from './entity-hero';

export function EntityHeroPage({ kind, name, entity, feedNew, feedHost, actions, helpers }: EntityHeroProps) {
  const people = isPeople(kind);
  const company = isCompany(kind);
  const facts = kind === 'performer' ? factRows(entity.profile) : [];
  const links = heroLinks(entity, kind);
  const marks = entryMarks(entity);
  const costars = kind === 'agency' ? [] : (entity.related_performers || []);
  const linkRow = useRef<HTMLDivElement>(null);
  const costarRow = useRef<HTMLDivElement>(null);
  /* 同台艺人与窄屏那排外链都是 `overflow-x:auto` 加隐藏滚动条：能滚，但鼠标没有一个够得着的
     入口，所以登记全站横向行那套拖动加滚轮映射。外链那排宽屏下换行，组件量得出不溢出。 */
  useEffect(() => { helpers.wireScroller(linkRow.current) }, [helpers, links.length]);
  useEffect(() => { helpers.wireScroller(costarRow.current) }, [helpers, costars.length]);

  return (
    <>
      <section data-entity-card="" aria-label="资料">
        <div data-entity-profile={facts.length ? 'facts' : ''}>
          <div data-entity-portrait-wrap="">
            <Portrait kind={kind} name={name} helpers={helpers} people={people} company={company} />
            {people && entity.id ? (
              <span data-avatar-picker="">
                <AvatarPicker kind={kind} entityId={Number(entity.id)} name={entity.canonical_name || name}
                  onPicked={actions.avatarPicked} />
              </span>
            ) : null}
          </div>
          <div data-entity-identity="">
            <div data-entity-title="">
              <h2>{entity.canonical_name}</h2>
              <NamePicker current={entity.canonical_name} choices={nameChoices(entity)}
                onChoose={actions.chooseName} onAddAlias={actions.addAlias} />
            </div>
            <AliasLine kind={kind} entity={entity} actions={actions} />
            {links.length ? (
              <div ref={linkRow} data-entity-links="">{links.map((link, at) => <HeroLinkView key={at} link={link} />)}</div>
            ) : null}
            {marks.length || entity.feed ? <EntryMarks entity={entity} actions={actions} helpers={helpers} /> : null}
          </div>
          {facts.length ? (
            <dl data-entity-facts="">
              {facts.map((row) => (
                <FactRowView key={row.label} glyph={row.glyph} label={row.label} clip={row.clip}>
                  {row.tags ? <FactTags tags={row.tags} />
                    : row.parts.map((part, at) => (
                      <span key={at} data-fact-tone={part.tone === 'plain' ? undefined : part.tone}>
                        {at ? ' ' : ''}{part.text}
                      </span>
                    ))}
                </FactRowView>
              ))}
            </dl>
          ) : null}
        </div>
        {costars.length ? (
          <div data-entity-foot="" aria-label="同台艺人">
            <div ref={costarRow} data-related-people="">
              {costars.map((person) => (
                <button key={person.k} type="button" data-related-performer={person.k}
                  onClick={() => actions.openEntity('performer', person.k)}>
                  <span data-hero-ring="" dangerouslySetInnerHTML={{
                    __html: `<span>${esc(person.k.slice(0, 1))}</span>${helpers.costarImg(person)}` }} />
                  <span data-hero-costar-name="">{person.k}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </section>
      {/* 新作那一行摆在壳留好的 `section.feednew[data-feed-new]` 里，与首页那一行同一个组件。 */}
      {feedHost ? createPortal(<FeedNewRow feedNew={feedNew} host={feedHost} wire={helpers.wireFeedRow}
        act={(feedId, action) => actions.feedAction(feedId, action)} />, feedHost) : null}
    </>
  );
}

/** 大位：公司取自己的标识（方框），人取实体图或代表作头像（圆框）；一环都取不到就只剩首字母。 */
function Portrait({ kind, name, helpers, people, company }: {
  kind: string; name: string; helpers: EntityHeroHelpers; people: boolean; company: boolean;
}) {
  /* 图只拼一次：兜底链摘掉的 `<img>`、人脸放大写进去的尺寸都留在节点上，重画时不能按
     同一段 HTML 再盖回去（`dangerouslySetInnerHTML` 只在字符串变了时才重写）。 */
  const [html] = useState(() => `${helpers.portraitImg()}<span>${esc(name.slice(0, 1))}</span>`);
  return (
    <div data-entity-portrait={people ? 'round' : 'square'} data-fit-native={company ? 'mark' : 'portrait'}
      data-entity-kind={kind} dangerouslySetInnerHTML={{ __html: html }} />
  );
}

/** 名字下面那一行。女优页分三项，各带一枚图标：视频数、事务所、别名（读音在最前）；其余种类
 *  仍是一行字：别名 · 视频数 · 归属。事务所是身份信息，不是链接的标签；账本里有这家的实体时
 *  给去处，只有采到的原文时只写名字。 */
function AliasLine({ kind, entity, actions }: { kind: string; entity: EntityHeroData; actions: EntityHeroActions }) {
  const agency = agencyOf(entity);
  const go = (target: string, to: string) => (event: MouseEvent) => {
    event.preventDefault();
    actions.openEntity(target, to);
  };
  const agencyNode = agency ? (agency.linked
    ? <a href={entityPath('agency', agency.name)} data-agency={agency.name} onClick={go('agency', agency.name)}>{agency.name}</a>
    : agency.name) : null;
  const count = <><b>{entity.asset_count.toLocaleString()}</b> 个视频</>;
  if (kind === 'performer') {
    const line = nameLine(entity.name_groups);
    return (
      <div data-entity-alias="meta">
        <span data-meta-item="" title="视频"><Glyph name="film" /><span>{count}</span></span>
        {agencyNode ? <span data-meta-item="" title="事务所"><Glyph name="briefcase" /><span>{agencyNode}</span></span> : null}
        {line ? (
          <div data-meta-item="names">
            <Glyph name="id-card" />
            <span data-alias-names="" title="别名">{line.names.map((one, at) => <span key={at}>{one}</span>)}</span>
            {line.rest > 0 ? (
              <MorePop id="entityAliasPop" hook="alias" rest={line.rest} label={`另外 ${line.rest} 个别名`}
                heading={`${line.total} 个别名`}>
                <dl>
                  {(entity.name_groups?.groups || []).map((group, at) => (
                    <NameGroup key={at} label={group.label} names={group.names} />
                  ))}
                </dl>
              </MorePop>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }
  const aliases = entity.display_aliases || [];
  /* 事务所页数的是人，不是片；片商页同理，旗下有几个 label 是它自己的读数（ADR-0051）。 */
  const members = kind === 'agency'
    ? <> · <b>{(entity.member_count || 0).toLocaleString()}</b> 位艺人</>
    : (entity.labels || []).length ? <> · <b>{entity.labels!.length.toLocaleString()}</b> 个厂牌</> : null;
  const maker = entity.maker;
  return (
    <div data-entity-alias="">
      {aliases.length ? `${aliases.join(' / ')} · ` : ''}{count}{members}
      {agencyNode ? <> · {agencyNode}</> : null}
      {maker ? <> · <a href={entityPath('studio', maker.name)} data-studio-link={maker.name}
        onClick={go('studio', maker.name)}>{maker.name}</a></> : null}
    </div>
  );
}

function NameGroup({ label, names }: { label?: string; names: { name: string; reading?: string }[] }) {
  return (
    <>
      {label ? <dt>{label}</dt> : null}
      <dd data-wide={label ? undefined : ''}>
        {names.map((entry, at) => <span key={at}>{entry.name}{entry.reading ? <small>{entry.reading}</small> : null}</span>)}
      </dd>
    </>
  );
}

function FactRowView({ glyph, label, clip, children }: { glyph: string; label: string; clip?: string; children: ReactNode }) {
  return (
    <>
      <dt><Glyph name={glyph} />{label}</dt>
      <dd data-fact={glyph === 'tags' ? 'tags' : clip ? 'clip' : glyph === 'calendar-range' ? 'num' : undefined}
        title={clip}>{children}</dd>
    </>
  );
}

/** 站上的标签只是读数，不是这一页的筛选，所以是标签的脸、不接点击。 */
function FactTags({ tags }: { tags: string[] }) {
  const { shown, rest } = shownTags(tags);
  return (
    <>
      {shown.map((tag) => <span key={tag} data-fact-tag="">{tag}</span>)}
      {rest ? (
        <MorePop id="entityTagPop" hook="fact" rest={rest} label={`另外 ${rest} 个标签`} heading={`${tags.length} 个标签`}>
          <div data-fact-tags="">{tags.map((tag) => <span key={tag} data-fact-tag="">{tag}</span>)}</div>
        </MorePop>
      ) : null}
    </>
  );
}

/** 链接前那枚圆标。站点圆标是别人服务器上的位图，取不到时 `data-drop="self"` 把 img 撤掉、
 *  露出底下那枚地球，所以这一格是遗留层的 HTML。 */
function LinkIcon({ mark }: { mark: LinkMark }) {
  if ('brand' in mark) return <span data-link-icon="brand"><Glyph name={mark.brand} /></span>;
  const html = icon('globe') + ('site' in mark
    ? `<img src="${esc(mark.site)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-drop="self">` : '');
  return <span data-link-icon="" dangerouslySetInnerHTML={{ __html: html }} />;
}

/** 外链排成一行次级按钮：36px 高、一圈线。纯图标的链接自己不带可读文字，名字留在 title 与
 *  读屏名称里；官网那种「点之前看不出是谁」的链接才写字。 */
function HeroLinkView({ link }: { link: LinkView }) {
  switch (link.type) {
    case 'icon':
      return (
        <a data-link="icon" href={link.url} target="_blank" rel="noreferrer" title={link.title} aria-label={link.title}>
          <LinkIcon mark={link.mark} />
        </a>
      );
    case 'gone':
      /* 已隐退女优的失效链接留在原位、不可点：去敲一个停放域名只会招来杀毒软件告警。 */
      return (
        <span data-link="gone" tabIndex={0} title={link.title} aria-label={link.title}>
          <LinkIcon mark={{ globe: true }} />
        </span>
      );
    case 'private':
      return (
        <span data-link="private" title="私人馆藏来源记录，不直接打开下载页">
          <LinkIcon mark={{ globe: true }} /><span data-link-label="">来源 · {link.label}</span>
        </span>
      );
    default:
      return (
        <a data-link="url" href={link.url} target="_blank" rel="noreferrer" title={link.title}>
          <LinkIcon mark={link.mark} /><span data-link-label="">{link.text}</span>
        </a>
      );
  }
}

/** 看片的那一行：JavDB 与 MISSAV 两站自己的标识，后面是订阅新作的开关。
 *
 *  MISSAV 站上没有图形标识，它的标题就是排出来的字：Halant 500、`MISS` 跟页面墨色、`AV` 用
 *  它的粉。一位女优在 javdb 有两个演员页是常事，第二枚在标识后面缀服务端编好的序号。 */
function EntryMarks({ entity, actions, helpers }: {
  entity: EntityHeroData; actions: EntityHeroActions; helpers: EntityHeroHelpers;
}) {
  const [following, setFollowing] = useState(!!entity.feed?.following);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  /* 写回失败时开关留在原位，失败回执由壳发；成功才发过去时的回执，撤销是另一次真实写回。 */
  const write = async (on: boolean): Promise<boolean> => {
    if (busyRef.current) return false;
    busyRef.current = true;
    setBusy(true);
    try {
      await actions.follow(on);
      setFollowing(on);
      return true;
    } catch {
      return false;
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };
  const toggle = async (on: boolean) => {
    if (!await write(on)) return;
    helpers.receipt(on ? '已订阅新作' : '已取消订阅新作', { undo: async () => { await write(!on) } });
    if (on) actions.refreshFeedAfterCheck();
  };
  return (
    <div data-entry-marks="">
      {entryMarks(entity).map((mark, at) => (
        <a key={at} data-entry-mark="" href={mark.url} target="_blank" rel="noreferrer" title={mark.label} aria-label={mark.label}>
          {mark.mark ? <Glyph name={mark.mark} /> : <span data-missav-mark=""><span>MISS</span><span>AV</span></span>}
          {mark.ordinal ? <span data-entry-ordinal="">{mark.ordinal}</span> : null}
        </a>
      ))}
      {entity.feed ? <FeedSwitch following={following} busy={busy} onToggle={(on) => { void toggle(on) }}
        tip={entityFeedTip(following)} /> : null}
    </div>
  );
}
