import { describe, expect, it } from 'vitest';
import { radarChart, rankedChart, statCardBody, distributionChart, jobProgressHtml } from '../src/board-metrics';
describe('指标与图表',()=>{
  it('分布图忽略空值且扇区以总量归一',()=>{
    expect(distributionChart([],'分布')).toBe('');
    const html=distributionChart([{name:'甲',score:1},{name:'乙',score:3}],'分布');
    expect(html).toContain('stroke-dasharray="25 75"');expect(html).toContain('stroke-dashoffset="-25"');
  });
  it('任务进度不虚构未知总量，并限制服务端瞬时越界值',()=>{
    expect(jobProgressHtml('扫描',1,0)).toBe('');
    expect(jobProgressHtml('扫描',11,10)).toContain('aria-valuenow="10"');
    expect(jobProgressHtml('扫描',-1,10)).toContain('aria-valuenow="0"');
  });
  it('指标保留读数和来源且转义外部标签',()=>{
    const html=statCardBody('<来源>','12','当前记录','database');
    expect(html).toContain('&lt;来源&gt;');expect(html).toContain('>12</b>');expect(html).not.toContain('arrow-up');
  });
  it('排名排除无效读数，按强弱排列且不修改原数组',()=>{
    const rows=[{name:'少',score:2},{name:'<多>',score:10},{name:'未知',score:NaN}];
    const html=rankedChart(rows,'排名');expect(html.indexOf('&lt;多&gt;')).toBeLessThan(html.indexOf('少'));
    expect(html).toContain('width:20.00%');expect(html).not.toContain('NaN');expect(rows[0]!.name).toBe('少');
  });
  it('雷达图只在至少三个真实维度时出现，并保留可访问读数',()=>{
    expect(radarChart([{name:'单一',score:1}],'口味')).toBe('');
    const html=radarChart([{name:'甲',score:1},{name:'乙',score:2},{name:'丙',score:3}],'口味');
    expect(html).toContain('role="img"');expect(html).toContain('丙 3');expect(html).not.toContain('NaN');
  });
});
