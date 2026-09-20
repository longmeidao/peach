/* 配置页（`/configuration`，也挂在设置弹层的「这台电脑」里）：四个分区排成一条窄列，
 * 每组一个小标题。服务端按两道门放行，不能编辑时「媒体」那一组只留一句原因。
 *
 * 遗留壳按 `.configgroup` 小标题把后面的兄弟节点切进左栏页签（`web/app.js` 的
 * `configTabItems`），所以标题和分区必须是 `.configpage` 的直接子节点、交替排列，
 * 没有内容的组连标题一起省略。设置弹层挂完这一页紧接着就读它，所以第一帧要同步落到
 * DOM 上：`../entry.tsx` 的 `mounter` 用 `flushSync` 画第一帧。 */
import { useQuery } from '@tanstack/react-query';

import { errorMessage } from '../../api';
import type { ConfigurationGroupProps, ConfigurationProps } from '../bundle';
import { Note } from '../components/note';
import { CONFIGURATION_KEY, fetchConfiguration } from './configuration';
import { GeneralSettings } from './general-settings';
import { MaintenanceSettings } from './maintenance-settings';
import { MediaSettings } from './media-settings';
import { NetworkSettings } from './network-settings';

export function ConfigurationPage({ receipt }: ConfigurationProps) {
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
  const network = Boolean(data.peach_proxy || data.access || data.tunnel);
  return (
    <div className="configpage">
      {data.startup ? <h2 className="configgroup">通用</h2> : null}
      {data.startup ? <GeneralSettings {...group} /> : null}
      <h2 className="configgroup">媒体</h2>
      <MediaSettings {...group} />
      {network ? <h2 className="configgroup">网络与访问</h2> : null}
      {network ? <NetworkSettings {...group} /> : null}
      <h2 className="configgroup">更新与维护</h2>
      <MaintenanceSettings {...group} />
    </div>
  );
}
