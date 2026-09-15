/* React 子树唯一的 TanStack Query 客户端（ADR-0031「前端基础库随页面引入」）。
 *
 * 一个客户端服务所有 React 根：页面级 `prefetch` 先把首屏写进缓存，组件挂上去之后
 * `useQuery` 直接读到同一份。两个客户端会让「取完数才画」的那一次取数落在另一个缓存里，
 * 组件挂载时又发一遍。 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /* 请求都打本机的 `/api/...`。浏览器的 online 标记说的是外网，断了外网它就翻 false，
         Query 默认会把本机请求也挂起成 paused——页面于是停在旧数据上，什么都不说。 */
      networkMode: 'always',
      /* 不重试。失败的原因是服务没起、账本只读或者迁移还没跑，同一秒里再问三遍得到的是
         同一句话，只把它推迟几秒显示；真正的重试是页面自己的轮询，下一轮就到。 */
      retry: 0,
      /* 焦点回来不自动重取：需要新数据的页面自己按内容定轮询节律（活动页是 2 秒／10 秒），
         再加一条焦点触发就是同一份数据两个节律。对外来源的采集与追更一律显式触发，
         更不能因为切回标签页就发出去。要即时刷新的页面自己在 `useQuery` 里打开。 */
      refetchOnWindowFocus: false,
      /* 挂载不重取、错了也不重试：每次进页面都是遗留层先 `prefetch` 再挂载（`islands.ts`
         的 React 档），组件挂上去时缓存里那一份就是刚取回来的。默认值会在同一次进入里
         紧接着再发一遍同样的请求；失败那次还会再失败一遍，错误反而晚一个来回才显示。 */
      refetchOnMount: false,
      retryOnMount: false,
    },
  },
});
