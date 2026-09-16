/* 创作者别名：同一个人在几个站上用几个名字，合并之后按一位创作者归组。
 *
 * 待合并是带依据的候选，合并永远由人点：服务端不自行升级，页面也不替他勾。 */
import { useState } from 'react';
import { RiCloseLine, RiUserLine } from '@remixicon/react';
import { useMutation } from '@tanstack/react-query';
import { confirmModal } from '@peach/legacy/ui';

import { Button } from '@/components/base/buttons/button';
import { Checkbox } from '@/components/base/checkbox/checkbox';
import { Input } from '@/components/base/input/input';
import {
  Table, TableBody, TableCell, TableColumn, TableHeader, TableRow,
} from '@/components/base/table/table';

import { errorMessage } from '../../api';
import { EmptyState } from '../components/empty-state';
import { ErrorText, FieldLabel } from '../settings/section';
import { busyProps } from '../settings/use-action';
import {
  addAlias, reloadFollowManage, removeAlias,
  type AliasGroup, type AliasSuggestion,
} from './follow-manage';

const REMOVE_BODY = (alias: string) => `将移除别名「${alias}」，对应来源恢复为独立创作者组。`;

export interface AliasManagerProps {
  groups: AliasGroup[];
  suggestions: AliasSuggestion[];
  readOnly: boolean;
  toast(message: string): void;
}

/** 一条待合并的身份：一个别名只可能归进一个规范名，所以用别名本身当键。 */
const suggestionKey = (item: AliasSuggestion) => item.alias;

export function AliasManager({ groups, suggestions, readOnly, toast }: AliasManagerProps) {
  const [selected, setSelected] = useState<ReadonlySet<string>>(new Set<string>());
  const [problem, setProblem] = useState('');
  const [canonical, setCanonical] = useState('');
  const [alias, setAlias] = useState('');

  /* 合并按顺序一条一条发：一次失败要报出「还有几组没合」，而并发发出去的话，说不清
     停在了哪里。 */
  const merge = useMutation({
    mutationFn: async (items: AliasSuggestion[]) => {
      let done = 0;
      for (const item of items) {
        try {
          await addAlias(item.canonical, item.alias);
        } catch (cause) {
          /* 半路断了要说清停在哪儿：已经合上的那几组先落回列表里去掉，再点一次只发剩下的。 */
          if (done) void reloadFollowManage();
          throw new Error(`${errorMessage(cause)}（还有 ${items.length - done} 组没有合并）`);
        }
        done += 1;
      }
      return { done, items };
    },
    onSuccess: (result) => {
      setProblem('');
      setSelected(new Set());
      void reloadFollowManage();
      toast(`已合并 ${result.done} 组创作者别名`);
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  const save = useMutation({
    mutationFn: (pair: { canonical: string; alias: string }) => addAlias(pair.canonical, pair.alias),
    onSuccess: () => {
      setProblem('');
      setCanonical('');
      setAlias('');
      void reloadFollowManage();
      toast('已保存创作者别名');
    },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  const drop = useMutation({
    mutationFn: (name: string) => removeAlias(name),
    onSuccess: () => { setProblem(''); void reloadFollowManage(); toast('已移除创作者别名') },
    onError: (cause) => setProblem(errorMessage(cause)),
  });

  const mergeSome = (items: AliasSuggestion[], all: boolean) => {
    if (!items.length) return;
    void confirmModal({
      title: all ? '合并全部创作者别名' : '合并所选创作者别名',
      body: `将合并以下 ${items.length} 组创作者：${items.map(
        (item) => `「${item.alias}」归入「${item.canonical}」`).join('；')}。`,
      confirmLabel: all ? '合并全部别名' : '合并所选别名',
      onConfirm: () => merge.mutateAsync(items),
    });
  };

  const chosen = suggestions.filter((item) => selected.has(suggestionKey(item)));
  const allChosen = suggestions.length > 0 && chosen.length === suggestions.length;
  const busy = busyProps(merge.isPending);

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-headline-medium text-text-primary">创作者别名</h3>

      <div className="flex flex-col gap-2">
        <FieldLabel>手动添加别名</FieldLabel>
        <div className="flex flex-wrap items-end gap-2">
          <Input aria-label="规范创作者名" placeholder="规范创作者名" value={canonical}
            onChange={setCanonical} isDisabled={readOnly} className="w-56" />
          <Input aria-label="平台别名" placeholder="平台别名" value={alias}
            onChange={setAlias} isDisabled={readOnly} className="w-56" />
          <Button variant="primary" size="small" disabled={readOnly || !canonical.trim() || !alias.trim()}
            {...busyProps(save.isPending)}
            onClick={() => save.mutate({ canonical: canonical.trim(), alias: alias.trim() })}>
            保存别名
          </Button>
        </div>
      </div>

      {problem ? <ErrorText>{problem}</ErrorText> : null}

      {suggestions.length ? (
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <FieldLabel>待合并</FieldLabel>
            <span className="mr-auto text-body-2-regular text-text-secondary">
              {`${suggestions.length} 组`}
            </span>
            <Button variant="secondary" size="small" disabled={readOnly || !chosen.length} {...busy}
              onClick={() => mergeSome(chosen, false)}>{`合并所选（${chosen.length}）`}</Button>
            <Button variant="primary" size="small" disabled={readOnly} {...busy}
              onClick={() => mergeSome(suggestions, true)}>{`全部合并（${suggestions.length}）`}</Button>
          </div>
          <Table aria-label="待合并创作者别名" size="sm">
            <TableHeader>
              <TableColumn id="select">
                {/* `slot={null}`：表格自带一个叫 selection 的插槽，摆进去的勾不声明归属就
                    会被它拦下报错。合并范围是这一屏自己的状态，不走 Table 的行选择。 */}
                <Checkbox slot={null} isSelected={allChosen} isIndeterminate={chosen.length > 0 && !allChosen}
                  aria-label="全选待合并别名"
                  onChange={(on) => setSelected(on
                    ? new Set(suggestions.map(suggestionKey))
                    : new Set<string>())} />
              </TableColumn>
              <TableColumn id="canonical">规范创作者</TableColumn>
              <TableColumn id="alias" isRowHeader>平台别名</TableColumn>
              <TableColumn id="evidence">依据</TableColumn>
              <TableColumn id="actions">操作</TableColumn>
            </TableHeader>
            <TableBody>
              {suggestions.map((item) => {
                const key = suggestionKey(item);
                return (
                  <TableRow key={key} id={key}>
                    <TableCell>
                      <Checkbox slot={null} isSelected={selected.has(key)}
                        aria-label={`选择别名 ${item.alias}，归入 ${item.canonical}`}
                        onChange={(on) => {
                          const next = new Set(selected);
                          if (on) next.add(key); else next.delete(key);
                          setSelected(next);
                        }} />
                    </TableCell>
                    <TableCell><b className="text-body-medium">{item.canonical}</b></TableCell>
                    <TableCell>{item.alias}</TableCell>
                    <TableCell>
                      <span className="text-body-2-regular text-text-secondary">{item.evidence}</span>
                    </TableCell>
                    <TableCell>
                      <Button variant="secondary" size="small" disabled={readOnly} {...busy}
                        onClick={() => mergeSome([item], false)}>合并</Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      ) : null}

      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <FieldLabel>已保存别名</FieldLabel>
          <span className="text-body-2-regular text-text-secondary">{`${groups.length} 组`}</span>
        </div>
        {groups.length ? (
          <Table aria-label="已保存创作者别名" size="sm">
            <TableHeader>
              <TableColumn id="canonical" isRowHeader>规范创作者</TableColumn>
              <TableColumn id="aliases">平台别名</TableColumn>
            </TableHeader>
            <TableBody>
              {groups.map((group) => (
                <TableRow key={group.canonical_key} id={group.canonical_key}>
                  <TableCell><b className="text-body-medium">{group.canonical_name}</b></TableCell>
                  <TableCell>
                    <span className="flex flex-wrap items-center gap-1.5">
                      {group.aliases.map((item) => (
                        <span key={item.key}
                          className="inline-flex items-center gap-1 rounded-md bg-background-secondary-default px-1.5 py-1 text-caption-1-medium text-text-secondary">
                          {item.name}
                          <Button variant="ghost" size="xs" iconOnly leadingIcon={RiCloseLine}
                            aria-label={`移除别名 ${item.name}`} disabled={readOnly}
                            {...busyProps(drop.isPending)}
                            onClick={() => void confirmModal({
                              title: '移除创作者别名', body: REMOVE_BODY(item.name),
                              confirmLabel: '移除创作者别名',
                              onConfirm: () => drop.mutateAsync(item.name),
                            })} />
                        </span>
                      ))}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState icon={RiUserLine} title="还没有保存创作者别名">
            填写规范创作者名和平台别名以添加。
          </EmptyState>
        )}
      </div>
    </div>
  );
}
