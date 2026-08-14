# 资源管理流水线

从下载那一刻起接管资源，到进 Stash 可检索为止。全部本地运行，不外传任何数据。

## 目录约定

```
R:\Inbox\<批次ID>\              下载落地区（每次下载一个批次目录）
R:\Media\创作者\<创作者>\       媒体库（物理目录只按创作者分一层）
R:\Resources\Intake\
  ├─ manifest\<批次ID>.json     登记：时间/链接/密码/快照/入库映射
  ├─ snapshots\<批次ID>\        每个视频的关键帧接触表（视觉留档）
  ├─ logs\<批次ID>.log          处理日志
  ├─ quarantine\<批次ID>\       解不开或可疑的文件，不进库
  └─ passwords.txt              解压密码本，自动累积
R:\Resources\Tools\             本工具集
```

## 三步用法

### 1. 下载前登记（把易失信息先钉住）

```powershell
cd R:\Resources\Tools
.\rm-register.ps1 -Url "https://某站/xxx" -Password "解压密码" -Note "备注" -Title "页面标题"
```

输出一个批次ID和落地目录，**把下载的文件放进那个目录**。链接、时间、密码当场记录，事后不会想不起来。
已知创作者可直接 `-Creator "跳跳羊"`，跳过自动归类。

### 2. 下载后处理

```powershell
.\rm-process.ps1 -Batch B20260812-123832      # 处理指定批次
.\rm-process.ps1 -All                          # 处理 Inbox 下全部
.\rm-process.ps1 -Batch xxx -WhatIfOnly        # 只预览不动文件
```

依次做四件事：

- **递归解压**：自动从密码本逐个试密码，支持嵌套压缩包（默认最深 4 层）；解不开的移入 quarantine，不会静默丢掉
- **去伪装**：靠 magic bytes 判断真实类型并修正扩展名。改成 `.jpg` 的 mp4、改成 `.txt` 的 rar 都能认出来；magic bytes 认不出时用 ffprobe 兜底（裸 H.264 码流、冷门容器、故意做坏的文件头都能救回来）
- **快照**：每个视频抽 9 帧拼接触表存进 snapshots，日后不用打开文件就能认内容
- **归类转移**：拿 Stash 里的 Performer 名和别名对文件名（含所在子目录）做子串匹配，命中就进对应创作者目录，没命中进「待识别」

### 3. 入 Stash

```powershell
.\rm-import.ps1                # 扫描 + 打标 + 创作者归属
.\rm-import.ps1 -SkipScan      # 已扫描过，只补标签
.\rm-import.ps1 -WhatIfOnly    # 预览
```

## 创作者归集规则

**物理目录 = 频道主（拍摄者 / 账号主）**，不是出镜者。

有些频道是男性约多位女性，那就归到该男性名下（`91大屌哥`、`Timepasserby`、`Svj798ds`），
这些场景带 `男主频道` + `多女出镜` 标签。出镜女性**不合并**——能具名的（如 `猫猫碎冰冰` 之于 `趣趣`）
作为附加 Performer 挂在同一场景上，Stash 一个场景可挂多个 Performer；不具名的用描述性标签
（`秘书OL`、`JK制服`、`人妻` 等）承载。

Performer 的 `gender` 字段已区分频道主性别，可直接筛选。

## 标签体系

`rm-tagmap.ps1` 是词典，改它即可调整全库标签规则：

- `$TagMap`：关键词 → 标签。对**完整相对路径**匹配（含子目录名），不只是文件名
- `$DirTags`：目录级默认标签（如某创作者全部是 3D）
- `$Performers`：创作者目录 → 规范名 + 别名

技术类标签（4K/2K/1080P/720P、竖屏/横屏、高帧率、时长分档）**不靠文件名猜**，
直接从 Stash 的文件元数据推导，准确率高得多。

每个标签都带 booru 风格英文别名（`足交/footjob`、`内射/creampie`、`毒龙/rimjob,analingus`），
中英文都能搜。

### 关于行为类标签的准确度

部位词不等于行为。已拆成四层，别再混用：

| 标签 | 含义 | 英文别名 |
|---|---|---|
| `屁眼` | 仅涉及部位，未确认行为 | anus, ass |
| `毒龙` | 舔舐 | rimjob, analingus, ass_licking |
| `肛塞` | 道具，非性交 | butt_plug, anal_plug |
| `肛交` | 明确的肛门性交 | anal, anal_sex |

`肛交` 可以靠关键帧确认（插入状态在画面里持续存在）。
`内射` 靠关键帧不可靠——射精是几秒的瞬间，均匀抽帧大概率错过，需在末段 20% 密集抽帧。

## 辅助工具

| 脚本 | 用途 |
|---|---|
| `rm-contactsheet.ps1` | 按目录生成 4×4 接触表，用于认创作者水印 |
| `rm-indexsheet.ps1` | 每文件抽 1 帧、25 个一页，用于逐文件判定归属 |
| `rm-verify.ps1` | 对指定场景ID密集抽帧，用于确认具体行为 |
| `rm-covers.ps1` | 给每位创作者自动配封面（从其最高分辨率片子抽 5 帧，选信息量最高的） |

## 识别创作者的三条路子

按可靠性排序：

1. **画面水印**——最可靠。目录名可能是伪装（`梦比优斯奥特曼` 实为 MyElla，`电化学_金属腐蚀…` 实为梅麻呂3D），但转载者通常保留原作者烧录的水印
2. **作品名联网反查**——日系同人有效（`淫乱爆乳女教師` → 梅麻呂3D）
3. **文件名文本**——最不可靠，但可批量

⚠️ 区分**创作者水印**和**转载渠道水印**：`@FLshe11`、`@SFJT68`、`@hmfl8`、`@zupi8888`、
`52ywy.com`、`5snn.com`、`9P3456.com` 这些是电报群和盗版站，不是创作者。

## 注意

- 不要让 PLM（猫库）与 Stash 同时管理 `R:\Media`，两者都会自动移动路径，会互相破坏数据库关联
- 任何批量操作后核对总数与总字节：当前基准 **2,552 个文件 / 844,902,505,772 bytes**
- Stash 只绑 `127.0.0.1`，不要暴露端口

## Web 回归测试

Peach 的数据层测试全部使用临时 SQLite，不会读写真实 `ledger.db`：

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m unittest discover `
  -s R:\Resources\Tools\tests -p 'test_*.py' -v
```

修改 `rm-web.py` 的筛选、播放埋点、反馈或鉴权后，至少先跑这一组测试。
