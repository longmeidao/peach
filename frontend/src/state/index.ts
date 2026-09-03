/* 跨岛共享状态的登记处（ADR-0022）。
 *
 * 约定只有三条，都是为了让「这份数据现在是什么」永远只有一个答案：
 *
 * 1. **一份共享数据一个文件**，文件名就是它的名字。岛自己的临时状态（展开、悬停、
 *    第几页）继续用 hooks，不进这里——那些东西没有第二个读者，搬进来只会让本来
 *    局部的东西变全局。
 * 2. **导出 `computed` 视图，不导出可写的 signal。** 写入只能通过该文件导出的函数，
 *    所以「谁改了它」在源码里数得出来。组件里直接赋值会抛 TypeError。
 * 3. **取数归 store。** `ensure` 是「读一次就够」，已有数据直接给；`refresh` 是
 *    「重新取」，页面刷新和遗留层写完数据之后走它。
 *
 * 遗留层（`web/app.js`）改完数据要通知岛时，用下面的 `refreshStore(name)`：它按名字
 * 拿 store，不需要知道函数名，和 `mountIsland(name, ...)` 同一种用法。挂载中的岛靠
 * signal 自己重画，不需要被重新挂载一遍。 */
import { refreshQualityGoals, resetQualityGoals } from './quality-goals';

const STORES = {
  'quality-goals': { refresh: refreshQualityGoals, reset: resetQualityGoals },
} as const;

export type StoreName = keyof typeof STORES;

/** 已登记的共享 store。遗留层与测试用它核对名字，不必知道注册表结构。 */
export const storeNames = (): StoreName[] => Object.keys(STORES) as StoreName[];

/** 让一份共享数据重新取一次。名字不认识时抛错，不静默什么都不做。
 *
 * 返回的 promise 在取数失败时**不**抛：失败已经落进 store 的错误态、显示在屏幕上了，
 * 而调用点在遗留层是 fire-and-forget，再抛一次只会变成没人接的 rejection。 */
export async function refreshStore(name: StoreName): Promise<boolean> {
  const store = STORES[name] as { refresh(): Promise<unknown> } | undefined;
  if (!store) throw new Error(`未登记的共享 store：${String(name)}`);
  try {
    await store.refresh();
    return true;
  } catch {
    return false;
  }
}

/** 把所有共享 store 清回未读状态。只给测试之间做隔离用，所以不从 `islands.ts` 再导出
 *  一次——产物的对外接口只有遗留层真正要调的那几个。 */
export function resetStores(): void {
  for (const store of Object.values(STORES)) store.reset();
}
