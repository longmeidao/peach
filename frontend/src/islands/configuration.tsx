/* 配置页（`/configuration`，也挂在设置弹层的「这台电脑」里）的外壳。
 *
 * 数据契约在 `/api/configuration`（`src/peach/routes_configuration.py`）。分区本身是 React 子树
 * （`src/react/settings/`）；外壳只取首屏数据、画分组小标题，每组交给一个 `ReactSlot`。
 * 遗留层的分区 tab（`web/app.js` 的 `configTabItems`）按 `.configgroup` 小标题把后面的节点切进
 * 面板，所以小标题和槽位要在 Preact 同步画出来的这一层，不能等 React 产物加载完才出现。 */
import { noteHtml } from '@peach/legacy/ui';
import type { ConfigurationData, ConfigurationGroupProps } from '@peach/react';

import { apiGet } from '../api';
import { CONFIGURATION_URL } from '../configuration-endpoints';
import { ReactSlot } from '../react-slot';

export type { ConfigurationData };

export interface ConfigurationProps {
  /** 保存成功后的过去时回执（遗留层的 Toast）。 */
  receipt(message: string): void;
}

export const loadConfiguration = (
  _props: ConfigurationProps,
  signal: AbortSignal,
): Promise<ConfigurationData> => apiGet<ConfigurationData>(CONFIGURATION_URL, signal);

type State = { data: ConfigurationData | null; error: string };

export function Configuration({ receipt, data, error }: ConfigurationProps & State) {
  if (error || !data) {
    return <div class="configpage" dangerouslySetInnerHTML={{ __html: noteHtml(error || '没有读到配置', { variant: 'error', label: '打不开配置' }) }} />;
  }
  const props: ConfigurationGroupProps = { data, receipt };
  return (
    <div class="configpage">
      {data.startup ? <h2 class="configgroup">通用</h2> : null}
      {data.startup ? <ReactSlot mount="mountGeneralSettings" props={props} /> : null}
      <h2 class="configgroup">媒体</h2>
      <ReactSlot mount="mountMediaSettings" props={props} />
      {data.peach_proxy || data.access ? <h2 class="configgroup">网络与访问</h2> : null}
      {data.peach_proxy || data.access ? <ReactSlot mount="mountNetworkSettings" props={props} /> : null}
      <h2 class="configgroup">更新与维护</h2>
      <ReactSlot mount="mountMaintenanceSettings" props={props} />
    </div>
  );
}
