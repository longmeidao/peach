/* 路由匹配：路径字符串进、参数出。不碰 DOM，也不认识任何一个页面函数。

   以前「这个路径是哪一屏」这件事在 app.js 里写了七遍：`restoreRoute()` 一条
   二十五分支的 if 链，`navTo`／`navOn`／`openManage`／`manageSection`／
   `reloadCurrentSurface`／`refreshAll` 各自再抄一份自己关心的那几条。加一屏要改
   七处，漏一处的症状各不相同：URL 能进但侧栏不亮、点进去了但换一批把你扔回统计页、
   批量操作后回到首页而不是刚才那一屏。真实踩过的就有抽屉漏了追更和播放列表那次。

   现在只有一张 ROUTES 表（在 app.js 里，因为它要引用各个 `open*`），匹配与取参
   这段纯逻辑放在这里，可以单独读、单独测。

   `match` 的写法只有三种，故意不上正则——路由是给人读的清单，不是模式语言：

   - `'/stats'`：精确路径。
   - `'/item/:id'`：`:name` 吃掉一段，且只吃数字。原来每条动态路由都自己写
     `/^\d+$/.test(parts[1]||'')`，忘写的那条会把 `/item/abc` 当合法 id 送进
     `+parts[1]` 变成 `NaN`。
   - `'/performers/:name*'`：`:name*` 吃掉剩下的全部段，至少一段。女优名字里有
     斜杠，所以实体页那条必须是「剩下全部」，不是「下一段」。 */

const PARAM = /^:([A-Za-z_]\w*)(\*)?$/;

/* 匹配成功返回参数对象（可能是空对象，它仍然是真值），失败返回 null。 */
export function matchPath(pattern, path) {
  const want = String(pattern).split('/').filter(Boolean);
  const got = String(path).split('/').filter(Boolean);
  const params = {};
  for (let i = 0; i < want.length; i += 1) {
    const named = PARAM.exec(want[i]);
    if (!named) {
      if (want[i] !== got[i]) return null;
      continue;
    }
    const [, name, greedy] = named;
    if (greedy) {
      const tail = got.slice(i).join('/');
      return tail ? { ...params, [name]: tail } : null;
    }
    if (!/^\d+$/.test(got[i] || '')) return null;
    params[name] = Number(got[i]);
  }
  return got.length === want.length ? params : null;
}

/* 先登记先匹配。表里的顺序即优先级，所以精确路径写在同前缀的动态路径前面。 */
export function matchRoute(routes, path) {
  for (const route of routes) {
    const params = matchPath(route.match, path);
    if (params) return { route, params };
  }
  return null;
}

/* document.title 用的标签。`title` 可以是字符串，也可以是拿参数算的函数——
   实体页的标题就是路径里那个名字本身。没有 title 的路由返回空串，由调用方
   决定兜底文案。 */
export function routeLabel(routes, path) {
  const hit = matchRoute(routes, path);
  if (!hit) return '';
  const { title } = hit.route;
  return String((typeof title === 'function' ? title(hit.params) : title) || '');
}
