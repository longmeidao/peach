/* ============================================================
 *  Pixiv 关注列表导出
 *  用法：登录 pixiv → 打开 https://www.pixiv.net/ → F12 控制台 → 粘贴运行
 *  产出：自动下载 pixiv-following.json
 *
 *  风控策略：
 *    - 用站点自己在用的 ajax 接口和 limit=24，请求形态与正常浏览一致
 *    - 每次请求间隔 1200~2000ms 随机抖动，不并发
 *    - 遇 429 自动退避（等待翻倍，最多重试 5 次）
 *    - 公开关注(rest=show)和私密关注(rest=hide)分两轮，中间多停 3 秒
 * ============================================================ */
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const jitter = (a, b) => a + Math.random() * (b - a);

  // 取自己的 user id
  let uid = null;
  try {
    uid = (document.querySelector('meta[name="global-data"]')
      && JSON.parse(document.querySelector('meta[name="global-data"]').content).userData.id) || null;
  } catch (e) {}
  if (!uid) {
    const m = document.documentElement.innerHTML.match(/"user_id":"(\d+)"/)
           || document.documentElement.innerHTML.match(/pixiv\.user\.id\s*=\s*"(\d+)"/);
    uid = m && m[1];
  }
  if (!uid) { console.error('取不到 user id，请确认已登录 pixiv'); return; }
  console.log('user id =', uid);

  async function get(url, tries = 0) {
    const r = await fetch(url, { credentials: 'include' });
    if (r.status === 429 || r.status === 403) {
      if (tries >= 5) throw new Error('多次被限流，已停止。请过一段时间再试。');
      const wait = 5000 * Math.pow(2, tries);
      console.warn(`被限流(${r.status})，等待 ${wait / 1000}s 后重试…`);
      await sleep(wait);
      return get(url, tries + 1);
    }
    if (!r.ok) throw new Error('HTTP ' + r.status + ' @ ' + url);
    return r.json();
  }

  const all = [];
  for (const rest of ['show', 'hide']) {          // 公开关注 + 私密关注
    let offset = 0, total = null;
    console.log(`--- 拉取 rest=${rest} ---`);
    while (total === null || offset < total) {
      const url = `https://www.pixiv.net/ajax/user/${uid}/following`
                + `?offset=${offset}&limit=24&rest=${rest}&tag=&lang=zh`;
      const j = await get(url);
      if (j.error) { console.error(j.message); break; }
      total = j.body.total;
      const users = j.body.users || [];
      for (const u of users) {
        all.push({
          rest,
          userId: u.userId,
          name: u.userName,
          comment: (u.userComment || '').slice(0, 200),
          following: u.following,
          homepage: `https://www.pixiv.net/users/${u.userId}`,
          // 该作者最近的作品标题，用于口味分析
          recentWorks: (u.illusts || []).slice(0, 5).map(i => ({
            id: i.id, title: i.title, tags: i.tags, url: i.url
          }))
        });
      }
      offset += 24;
      console.log(`  ${Math.min(offset, total)}/${total}`);
      if (users.length === 0) break;
      await sleep(jitter(1200, 2000));
    }
    await sleep(3000);
  }

  console.log(`合计 ${all.length} 位关注作者`);
  const blob = new Blob([JSON.stringify(all, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'pixiv-following.json';
  a.click();
  console.log('已下载 pixiv-following.json');
})();
