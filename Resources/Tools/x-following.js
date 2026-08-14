/* ============================================================
 *  X (Twitter) 关注列表 + Lists 导出
 *  用法：登录 x.com → 打开 https://x.com/<你的用户名>/following
 *        → F12 控制台 → 粘贴运行 → 脚本会自动滚动到底
 *  产出：自动下载 x-following.json
 *
 *  为什么用滚动抓 DOM 而不是调 GraphQL API：
 *    X 对 /i/api/graphql/* 的限流极其严格，短时间多次调用会直接锁读取权限
 *    （通常要等 15 分钟到数小时）。滚动页面走的是站点自己的分页节奏，
 *    风险低得多，代价是慢一些。
 *
 *  Lists 请另外跑一次：打开 https://x.com/<你的用户名>/lists 后再运行本脚本，
 *  它会自动识别当前是 following 页还是 lists 页。
 * ============================================================ */
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const jitter = (a, b) => a + Math.random() * (b - a);
  const isLists = location.pathname.endsWith('/lists');
  console.log(isLists ? '模式：Lists' : '模式：Following');

  const seen = new Map();

  function harvest() {
    if (isLists) {
      document.querySelectorAll('a[href*="/i/lists/"]').forEach(a => {
        const href = a.getAttribute('href');
        const id = (href.match(/\/i\/lists\/(\d+)/) || [])[1];
        if (!id) return;
        const txt = a.innerText.split('\n').filter(Boolean);
        if (!seen.has(id)) seen.set(id, {
          listId: id,
          name: txt[0] || '',
          meta: txt.slice(1).join(' | '),
          url: 'https://x.com' + href
        });
      });
    } else {
      document.querySelectorAll('[data-testid="UserCell"]').forEach(cell => {
        const a = cell.querySelector('a[href^="/"]');
        if (!a) return;
        const handle = a.getAttribute('href').replace(/^\//, '').split('/')[0];
        if (!handle || handle.startsWith('i')) return;
        const lines = cell.innerText.split('\n').filter(Boolean);
        if (!seen.has(handle)) seen.set(handle, {
          handle: '@' + handle,
          name: lines[0] || '',
          bio: lines.slice(2).join(' ').slice(0, 300),
          url: 'https://x.com/' + handle
        });
      });
    }
  }

  let lastCount = -1, stagnant = 0, rounds = 0;
  while (stagnant < 5 && rounds < 400) {
    harvest();
    if (seen.size === lastCount) stagnant++; else stagnant = 0;
    lastCount = seen.size;
    rounds++;
    if (rounds % 5 === 0) console.log(`  已收集 ${seen.size} 条（第 ${rounds} 轮）`);
    window.scrollBy(0, window.innerHeight * 0.85);
    await sleep(jitter(1500, 2600));          // 慢一点，别让 X 觉得是脚本
  }
  harvest();

  const out = [...seen.values()];
  console.log(`完成，共 ${out.length} 条`);
  const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = isLists ? 'x-lists.json' : 'x-following.json';
  a.click();
  console.log('已下载');
})();
