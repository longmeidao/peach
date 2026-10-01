/* 设置弹层「这台电脑」那一格的摘要卡：媒体库数、端口、更新状态，加一颗「打开配置页」。
 *
 * 设置弹层只放一行一个值、改完就生效的控件；要「保存配置」的多字段表单都在
 * `/configuration`（ADR-0050），这里只读同一份配置快照（`CONFIGURATION_KEY`）。
 * 灰卡由设置面板那一格 `[data-setting-group]` 画（`../settings-panel/`），这里只画卡里的读数与页脚。 */
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/base/buttons/button';

import { errorMessage } from '../../api';
import type { ConfigurationData } from '../bundle';
import { Note } from '../components/note';
import { CONFIGURATION_KEY, fetchConfiguration } from './configuration';
import { Fact, FactList, Footer, Stack } from './section';

export interface ConfigurationSummaryProps {
  /** 关掉设置面板、换到 `/configuration`。整页换成哪一屏归壳。 */
  openConfiguration(): void;
}

const updateLine = (data: ConfigurationData) => {
  const updates = data.updates;
  if (!updates) return '未取得';
  return updates.message ? `${updates.current_version} · ${updates.message}` : updates.current_version;
};

export function ConfigurationSummary({ openConfiguration }: ConfigurationSummaryProps) {
  const config = useQuery({
    queryKey: CONFIGURATION_KEY, queryFn: ({ signal }) => fetchConfiguration(signal),
  });
  const data = config.data;
  return (
    <div className="flex flex-col">
      {data
        ? <FactList>
            <Fact term="媒体库">{`${data.library_count} 个`}</Fact>
            <Fact term="端口">{String(data.port)}</Fact>
            <Fact term="更新">{updateLine(data)}</Fact>
          </FactList>
        : <Stack>
            <Note tone="error" title="配置读取失败">
              {config.error ? errorMessage(config.error) : '未取得配置，请刷新页面重试。'}
            </Note>
          </Stack>}
      <Footer status="媒体文件夹、端口、代理与更新在配置页上改。">
        <Button onClick={openConfiguration}>打开配置页</Button>
      </Footer>
    </div>
  );
}
