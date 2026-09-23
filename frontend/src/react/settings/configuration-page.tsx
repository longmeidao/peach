/* 配置页（`/configuration`）：这台运行 Peach 的电脑上那些要「保存配置」的多字段表单。
 * 四个分区排成一条窄列，每组一个小标题。服务端按两道门放行，不能编辑时「媒体」那一组只留
 * 一句原因。设置弹层里只有一张摘要卡指到这里（ADR-0050）。
 *
 * 遗留壳按 `.configgroup` 小标题把后面那一个兄弟节点切进页签（`web/app.js` 的
 * `configTabItems`），所以标题和分区必须是 `.configpage` 的直接子节点、交替排列，
 * 没有内容的组连标题一起省略。 */
import { useQuery } from '@tanstack/react-query';

import { errorMessage } from '../../api';
import type { ConfigurationGroupProps, ConfigurationProps } from '../bundle';
import { Note } from '../components/note';
import { CONFIGURATION_KEY, fetchConfiguration } from './configuration';
import { GeneralSettings } from './general-settings';
import { MaintenanceSettings } from './maintenance-settings';
import { MediaSettings } from './media-settings';
import { NetworkSettings } from './network-settings';

export function ConfigurationPage({ receipt, reopenTutorial }: ConfigurationProps) {
  const config = useQuery({
    queryKey: CONFIGURATION_KEY, queryFn: ({ signal }) => fetchConfiguration(signal),
  });
  const data = config.data;
  if (!data) {
    return (
      <div className="configpage">
        <Note tone="error" title="打不开配置">
          {config.error ? errorMessage(config.error) : '没有读到配置'}
        </Note>
      </div>
    );
  }
  const group: ConfigurationGroupProps = { data, receipt };
  const general = Boolean(data.startup || data.entry_links);
  const network = Boolean(data.peach_proxy || data.access || data.tunnel);
  return (
    <div className="configpage">
      {general ? <h2 className="configgroup">通用</h2> : null}
      {general ? <GeneralSettings {...group} /> : null}
      <h2 className="configgroup">媒体</h2>
      <MediaSettings {...group} />
      {network ? <h2 className="configgroup">网络与访问</h2> : null}
      {network ? <NetworkSettings {...group} /> : null}
      <h2 className="configgroup">更新与维护</h2>
      <MaintenanceSettings {...group} reopenTutorial={reopenTutorial} />
    </div>
  );
}
