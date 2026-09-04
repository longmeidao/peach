import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, rmSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checkOnly = process.argv.includes("--check");
const manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const lock = JSON.parse(readFileSync(join(root, "package-lock.json"), "utf8"));
const versions = manifest.devDependencies;
const expectedFiles = new Map();

const read = (...parts) => readFileSync(join(root, ...parts));
const text = (...parts) => read(...parts).toString("utf8");
// .gitattributes 让整仓签出 LF，而 npm 包里的许可证原文有 CRLF 的。照抄字节的话，
// 提交后签出来的那份和这里算出来的期望值差在换行上，--check 每次都报未同步。
const lfText = (...parts) => text(...parts).replace(/\r\n/g, "\n");
const sha256 = value => createHash("sha256").update(value).digest("hex").toUpperCase();
const integrity = name => lock.packages[`node_modules/${name}`]?.integrity || "未取得";
const stage = (path, value) => expectedFiles.set(path, Buffer.isBuffer(value) ? value : Buffer.from(value));

const copyPackageFiles = ({ packageName, vendorName, files, note }) => {
  const version = versions[packageName];
  const hashes = [];
  for (const [source, destination] of files) {
    const payload = read("node_modules", packageName, ...source.split("/"));
    const target = `web/vendor/${vendorName}/${version}/${destination}`;
    stage(target, payload);
    hashes.push(`- \`${destination}\` SHA-256：\`${sha256(payload)}\``);
  }
  const license = lfText("node_modules", packageName, "LICENSE");
  stage(`web/vendor/${vendorName}/${version}/LICENSE`, license);
  stage(`web/vendor/${vendorName}/${version}/ORIGIN.md`,
    `# ${packageName} ${version}\n\n` +
    `- npm 包：\`${packageName}@${version}\`\n` +
    `- npm lock integrity：\`${integrity(packageName)}\`\n` +
    `- 许可证：见同目录 \`LICENSE\`\n` +
    `${hashes.join("\n")}\n\n${note}\n`);
};

copyPackageFiles({
  packageName: "video.js",
  vendorName: "videojs",
  files: [
    ["dist/video.min.js", "video.min.js"],
    ["dist/video-js.min.css", "video-js.min.css"],
    ["dist/font/VideoJS.woff", "font/VideoJS.woff"],
    ["dist/lang/zh-CN.js", "lang/zh-CN.js"],
  ],
  note: "Peach 自托管固定版本，不依赖 CDN。直接 MP4 使用 Range，远端原生 MP4 可使用服务端 HLS 短片段；两者共用 Video.js 内置 VHS。",
});

copyPackageFiles({
  packageName: "swiper",
  vendorName: "swiper",
  files: [
    ["swiper-bundle.min.js", "swiper-bundle.min.js"],
    ["swiper-bundle.min.css", "swiper-bundle.min.css"],
  ],
  note: "Peach 自托管固定版本，不依赖 CDN。只有照片灯箱按需加载 Thumbs、Keyboard 与 Zoom；瀑布流不经过 Swiper。",
});

const lucideIcons = new Map([
  ["home", "home"], ["sliders-horizontal", "sliders-horizontal"], ["search", "search"],
  ["layout-grid", "layout-grid"], ["square-check-big", "square-check-big"],
  ["refresh-cw", "refresh-cw"], ["user-round", "user-round"], ["tags", "tags"],
  ["list-filter", "list-filter"], ["chart", "chart-no-axes-column"],
  ["settings", "settings"], ["gauge", "gauge"],
  ["history", "history"], ["sparkles", "sparkles"],
  ["x", "x"], ["folder-open", "folder-open"], ["info", "info"],
  ["hard-drive", "hard-drive"], ["globe", "globe"], ["rss", "rss"],
  ["thumbs-up", "thumbs-up"], ["thumbs-down", "thumbs-down"], ["eye", "eye"],
  ["eye-off", "eye-off"], ["grip-vertical", "grip-vertical"], ["trash", "trash-2"],
  ["plus", "plus"], ["minus", "minus"], ["check", "check"],
  ["rotate-ccw", "rotate-ccw"], ["rotate-cw", "rotate-cw"], ["maximize", "maximize"],
  ["chevron-left", "chevron-left"], ["chevron-right", "chevron-right"],
  ["chevron-up", "chevron-up"], ["chevron-down", "chevron-down"], ["heart", "heart"],
  ["upload", "upload"], ["database", "database"], ["play", "play"], ["clock", "clock"],
  ["external-link", "external-link"], ["bookmark-plus", "bookmark-plus"],
  ["bookmark", "bookmark"], ["gallery-vertical-end", "gallery-vertical-end"],
  ["notebook-pen", "notebook-pen"], ["search-x", "search-x"],
  ["file-archive", "file-archive"], ["file-audio", "file-audio"],
  ["file-stack", "file-stack"],
  // 名字和上游对不上的只有排序键：Peach 叫 `sort`，Lucide 叫 `sort-desc`。
  ["sort", "sort-desc"], ["arrow-up", "arrow-up"], ["arrow-down", "arrow-down"],
  ["calendar", "calendar"], ["download", "download"], ["monitor", "monitor"],
  ["ratio", "ratio"], ["sun", "sun"], ["moon", "moon"],
]);

// 自绘 symbol：没有上游可对，所以在这里逐个点名。下面那道分区检查要求雪碧图里
// 每一枚要么由某一套生成、要么写在这张名单上——漏一枚就会被当成忘了纳管。
const handDrawnIcons = new Set([
  "alert", "pics", "jav", "theater-enter", "theater-exit", "brand-x",
]);

const svgInner = source => {
  const match = source.match(/<svg[^>]*>([\s\S]*?)<\/svg>/);
  if (!match) throw new Error("上游 SVG 结构无法识别");
  return match[1].trim().split(/\r?\n/).map(line => line.trim()).join("");
};

let index = text("web", "index.html");
for (const [symbol, icon] of lucideIcons) {
  let inner = svgInner(text("node_modules", "lucide-static", "icons", `${icon}.svg`));
  if (symbol === "rss") inner = inner.replace('<circle cx="5" cy="19" r="1" />', '<circle cx="5" cy="19" r="1" fill="currentColor" stroke="none"/>');
  if (symbol === "grip-vertical") inner = inner.replaceAll(' r="1" />', ' r="1" fill="currentColor" stroke="none"/>');
  const pattern = new RegExp(`<symbol id="i-${symbol}" viewBox="0 0 24 24">[\\s\\S]*?<\\/symbol>`);
  if (!pattern.test(index)) throw new Error(`缺少 Lucide symbol：${symbol}`);
  index = index.replace(pattern, `<symbol id="i-${symbol}" viewBox="0 0 24 24">${inner}</symbol>`);
}

// Phosphor 是填充图标，Peach 全局是描边：填充声明写在 symbol 上，路径不改一个字，
// 换版本时不必再核每条 path 有没有被补过 fill。
// viewBox 也不原样照抄：每套图标在自己画格里留的白不一样，同样 15px 画出来一大一小。
// 这里的框是量出来的——把内容外框补到 Lucide 的 20/24 活区，字形按高、图形按长边。
const phosphorIcons = new Map([
  ["text-aa", { icon: "text-aa", viewBox: "-7.3 32.8 262.5 182.9" }],
  ["playlist", { icon: "playlist", viewBox: "10.4 10.5 259.2 259.2" }],
]);
for (const [symbol, { icon, viewBox }] of phosphorIcons) {
  const inner = svgInner(text("node_modules", "@phosphor-icons/core", "assets", "regular", `${icon}.svg`));
  const attrs = `viewBox="${viewBox}" fill="currentColor" stroke="none"`;
  const pattern = new RegExp(`<symbol id="i-${symbol}" ${attrs.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}>[\\s\\S]*?<\\/symbol>`);
  if (!pattern.test(index)) throw new Error(`缺少 Phosphor symbol：${symbol}`);
  index = index.replace(pattern, `<symbol id="i-${symbol}" ${attrs}>${inner}</symbol>`);
}

const healthInner = svgInner(text("node_modules", "healthicons", "public", "icons", "svg", "outline-24px", "contraceptives", "sperm.svg"));
const SPERM_VIEWBOX = "1.5 1.2 21.2 21.2";
index = index.replace(
  new RegExp(`<symbol id="i-sperm" viewBox="${SPERM_VIEWBOX}">[\\s\\S]*?<\\/symbol>`),
  `<symbol id="i-sperm" viewBox="${SPERM_VIEWBOX}">${healthInner}</symbol>`);
index = index.replace(/Lucide static [0-9.]+, ISC/, `Lucide static ${versions["lucide-static"]}, ISC`);
index = index.replace(/Health Icons sperm outline-24px, CC0\/public domain/,
  `Health Icons ${versions.healthicons} sperm outline-24px, CC0/public domain`);
index = index.replace(/Phosphor [0-9.]+ regular, MIT/,
  `Phosphor ${versions["@phosphor-icons/core"]} regular, MIT`);
index = index.replaceAll(/\/vendor\/videojs\/[0-9.]+\//g, `/vendor/videojs/${versions["video.js"]}/`);
stage("web/index.html", index);

let app = text("web", "app.js");
app = app.replaceAll(/\/vendor\/swiper\/[0-9.]+\//g, `/vendor/swiper/${versions.swiper}/`);
stage("web/app.js", app);

let webTests = text("tests", "test_web_ui.py");
webTests = webTests.replaceAll(/\/vendor\/videojs\/[0-9.]+\//g, `/vendor/videojs/${versions["video.js"]}/`);
webTests = webTests.replaceAll(/\/vendor\/swiper\/[0-9.]+\//g, `/vendor/swiper/${versions.swiper}/`);
stage("tests/test_web_ui.py", webTests);

let reuse = text("docs", "REUSE.md");
reuse = reuse.replace(/Video\.js [0-9.]+/, `Video.js ${versions["video.js"]}`);
reuse = reuse.replace(/Swiper [0-9.]+/, `Swiper ${versions.swiper}`);
stage("docs/REUSE.md", reuse);

stage("web/vendor/lucide-LICENSE.txt", lfText("node_modules", "lucide-static", "LICENSE"));
stage("web/vendor/lucide-ORIGIN.md",
  `# Lucide static ${versions["lucide-static"]}\n\n` +
  `- npm 包：\`lucide-static@${versions["lucide-static"]}\`\n` +
  `- npm lock integrity：\`${integrity("lucide-static")}\`\n` +
  `- 许可证：ISC；原文见 \`lucide-LICENSE.txt\`\n` +
  `- 消费者：\`web/index.html\` 内联的 ${lucideIcons.size} 个 symbol\n\n` +
  `雪碧图里另有 ${handDrawnIcons.size} 枚自绘 symbol（${[...handDrawnIcons].join("、")}）与 16 枚 player-* 前缀的播放器图标，都没有上游可对。\n` +
  "RSS 与拖动点保留填充修正，避免小圆点在全局描边样式下消失。\n");
stage("web/vendor/phosphor-LICENSE.txt", lfText("node_modules", "@phosphor-icons/core", "LICENSE"));
stage("web/vendor/phosphor-ORIGIN.md",
  `# Phosphor icons ${versions["@phosphor-icons/core"]}\n\n` +
  `- npm 包：\`@phosphor-icons/core@${versions["@phosphor-icons/core"]}\`\n` +
  `- npm lock integrity：\`${integrity("@phosphor-icons/core")}\`\n` +
  `- 许可证：MIT；原文见 \`phosphor-LICENSE.txt\`\n` +
  `- 消费者：\`web/index.html\` 内联的 ${phosphorIcons.size} 个 regular 权重 symbol\n\n` +
  "只在描边画法说不清那件事时才用这一套：`text-aa` 是字母表，`playlist` 是播放列表。\n" +
  "填充声明写在 symbol 上，压住全局的 `stroke:currentColor;fill:none`。\n");
stage("web/vendor/healthicons-LICENSE.txt", lfText("node_modules", "healthicons", "LICENSE"));
stage("web/vendor/healthicons-ORIGIN.md",
  `# Health Icons ${versions.healthicons}\n\n` +
  `- npm 包：\`healthicons@${versions.healthicons}\`\n` +
  `- npm lock integrity：\`${integrity("healthicons")}\`\n` +
  "- 许可证：npm 包为 MIT，图标由上游声明为 CC0/public domain；原文见 `healthicons-LICENSE.txt`\n" +
  "- 消费者：`web/index.html` 的 `sperm` outline-24px symbol\n");

// 雪碧图的分区检查。少了它，新画一枚 symbol 只会安静地待在 index.html 里，
// 换 Lucide 版本时不跟着刷新，也没人看得出它是自绘的还是忘了纳管。
const spriteSymbols = [...index.matchAll(/id="i-([a-z0-9-]+)"/g)].map(m => m[1]);
const owned = new Set([...lucideIcons.keys(), ...phosphorIcons.keys(),
  ...handDrawnIcons, "sperm"]);
const orphans = spriteSymbols.filter(
  name => !name.startsWith("player-") && !owned.has(name));
if (orphans.length) {
  throw new Error(`雪碧图里这些 symbol 没有归属，加进对应图标集或 handDrawnIcons：${orphans.join("、")}`);
}

const versionRoots = [
  ["web/vendor/videojs", versions["video.js"]],
  ["web/vendor/swiper", versions.swiper],
];
const problems = [];
for (const [path, expected] of expectedFiles) {
  const absolute = join(root, path);
  if (!existsSync(absolute) || !readFileSync(absolute).equals(expected)) problems.push(path);
}
for (const [path, version] of versionRoots) {
  const absolute = join(root, path);
  const actual = existsSync(absolute) ? readdirSync(absolute).sort() : [];
  if (actual.length !== 1 || actual[0] !== version) problems.push(`${path} 版本目录`);
}

if (checkOnly) {
  if (problems.length) {
    console.error(`前端固定依赖未同步：\n${problems.map(path => `- ${path}`).join("\n")}`);
    process.exit(1);
  }
  console.log(`前端固定依赖已同步：Video.js ${versions["video.js"]}、Swiper ${versions.swiper}、Lucide ${versions["lucide-static"]}、Phosphor ${versions["@phosphor-icons/core"]}、Health Icons ${versions.healthicons}`);
  process.exit(0);
}

for (const [path] of versionRoots) rmSync(join(root, path), { recursive: true, force: true });
for (const [path, payload] of expectedFiles) {
  const absolute = join(root, path);
  mkdirSync(dirname(absolute), { recursive: true });
  writeFileSync(absolute, payload);
}
console.log(`已更新 ${expectedFiles.size} 个固定依赖文件。`);
