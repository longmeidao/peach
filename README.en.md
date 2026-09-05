<p align="center">
  <img src="resources/peach-logo.png" alt="Peach" width="128">
</p>

<h1 align="center">Peach</h1>

<p align="center">A single-user, local-first personal media system</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/longmeidao/peach/test.yml?branch=master&amp;label=tests&amp;logo=githubactions&amp;logoColor=white" alt="tests"></a>
  <a href="https://github.com/longmeidao/peach/releases"><img src="https://img.shields.io/github/v/release/longmeidao/peach?include_prereleases&amp;label=release&amp;logo=github&amp;logoColor=white" alt="release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue?logo=gnu&amp;logoColor=white" alt="license"></a>
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/platform-Windows-0078D4?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xIDFoMTB2MTBIMXptMTIgMGgxMHYxMEgxM3pNMSAxM2gxMHYxMEgxem0xMiAwaDEwdjEwSDEzeiIvPjwvc3ZnPg%3D%3D" alt="Windows">
  <img src="https://img.shields.io/badge/platform-macOS-555555?logo=apple&amp;logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/18%2B-adult%20content-critical?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIj48cGF0aCBkPSJNMTIgMiAzIDZ2NmMwIDUgOSAxMCA5IDEwczktNSA5LTEwVjZ6TTEyIDd2Nm0wIDN2MSIvPjwvc3ZnPg%3D%3D" alt="18+ adult content">
</p>

<p align="center"><a href="README.md">中文</a> · English</p>

> **18+** Peach is for adults and manages an adult-content collection. The repository, its documentation and screenshots contain SFW material only; the boundaries are in "Scope and disclaimer" below.

Peach is a single-user, local-first personal media system, built for one person self-hosting on their own machines over a LAN — not for teams or public deployment. It indexes media you already own — local disks, CloudDrive mounts, followed online sources — and serves search, playback, profile pages, playlists, review and follow from one FastAPI process. The local SQLite ledger is the single source of truth and also stores viewing behavior and manual decisions; whatever CloudDrive, online sites or AI return is a candidate with provenance and confidence, and becomes truth only after the user reviews it.

Peach runs completely on a single machine and is pre-1.0. Windows and macOS are first-class platforms; Linux is not supported and has not been tested. Single-writer replication between machines is optional and off by default, and so far it has been verified in exactly one shape: a Windows writer with a macOS reader. The current runtime state and verification results are in [`docs/STATUS.md`](docs/STATUS.md), open work is in [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md), and development constraints start at [`AGENTS.md`](AGENTS.md).

## Core capabilities

- Browse the collection by item, performer, studio, creator, series and tag.
- Play local and cloud-drive media; incompatible containers get a deletable transcode cache, and original files are never rewritten.
- Save watch later, reasons for liking, watched state, automatic Mixes and persistent playlists.
- Review external metadata, identity, image and media-failure candidates through `/review`.
- Discover updates from the official FANBOX, SubscribeStar and Patreon channels, the Kemono/Pawchive/Coomer archive sites, Rule34Video, Rule34.xxx, Rule34 Paheal and F95zone; SimpCity's bot verification is not bypassed.
- Optional: replicate the ledger explicitly between two machines; on divergence the reader turns read-only, with no automatic merge.

## Data boundaries

The ledger is the source of truth for assets, identities, behavior and review decisions. CloudDrive, online sites and AI are adapters or candidate sources; none of them may write truth fields directly.

| Content | Location or rule |
| --- | --- |
| Database | `peach-data/database/ledger.db` |
| Media paths | The ledger always stores Windows drive letters; macOS translates them at read time |
| Credentials | `peach-data/secrets/`; never enter Git, logs or API responses |
| Derived images | Deletable and rebuildable; one-way sync Windows → macOS |
| Real writes | Only the current writer may write; migrations and irreversible operations require a backup and authorization first |
| Tests | Use temporary SQLite databases and temporary media only |

When replication is enabled, each machine keeps its own local working copy of the ledger; the shared directory is only a transfer point. Starting the service does not replicate anything; "Sync Ledger" and "Take over ledger writes" are explicit operations. The detailed design is in [`ADR-0017`](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md).

## Scope and disclaimer

- Peach is built for a personal collection of adult content (JAV, creator subscriptions and the
  like); the repository itself contains none of it. Screenshots in the README, the documentation and
  the website always use SFW demo data, never a real collection.
- The repository contains only code, documentation and pinned frontend dependencies. It ships no
  media, covers, thumbnails or metadata, and no copy of any site's data; what it indexes is the
  library the person running it already owns.
- Connectors access only sources the user is entitled to access, with credentials the user supplies.
  Peach does not bypass bot verification, paywalls or any access control: when it meets such a block
  it records "not obtained" — the fixed wording for a failed acquisition — and stops there.
- Titles, images and descriptions fetched from external sources remain the content and copyright of
  the respective sites and their creators. Peach stores them as candidates, keeps their provenance
  and confidence, and leaves verification to the user.

## Layout

```text
peach-app/
├─ src/peach/        FastAPI, media, ledger, migrations and providers
├─ web/              Frontend without a build step
├─ migrations/       Versioned, checksummed SQLite migrations
├─ scripts/          Build, check and batch-job entry points
├─ tests/            Isolated tests
├─ docs/             Status, architecture, reuse decisions and ADRs
├─ AGENTS.md         Shared entry point for Codex and Claude
└─ CLAUDE.md         Import entry point for Claude
```

The repository stores no media, databases, credentials, logs, `.venv`, build output or worktrees.

## Prerequisites

- **Python 3.12 or newer**: a hard requirement from `requires-python`; the maintainer runs 3.14, and CI tests both 3.12 and 3.14. Windows needs the py launcher (`py -3.14`, substitute the version you installed); in a console using the cp936 code page the CLI's Chinese output is garbled, and `PYTHONIOENCODING=utf-8` fixes it.
- **Git**: the editable install runs from a checked-out repository.
- **FFmpeg and ffprobe**: not distributed with the repository, which has no downloader for them either. Lookup order: the `PEACH_FFMPEG` / `PEACH_FFPROBE` environment variables → `<data root>/tools/ffmpeg/bin/ffmpeg(.exe)` and `ffprobe(.exe)` → `PATH`. Without them `/healthz` reports `ffmpeg: unavailable`, and frame extraction, contact sheets, probing and covers are all unavailable; browsing and playback of compatible formats still work.
- **openssl** (optional, HTTPS only): required to generate the local CA. On Windows it usually comes from Git for Windows (choose the option that puts the Unix tools on `PATH`). Without it `peach init` prints that no local CA was generated and completes normally; once installed, `peach init --force` fills it in.
- Node is not a runtime prerequisite; it only maintains the pinned frontend files (see "Dependency maintenance").

## Downloads

Windows testers can download `Peach-<version>-windows-x64.zip` from [GitHub Releases](https://github.com/longmeidao/peach/releases), extract the complete folder, and double-click `Peach.exe`. Choose a media folder in the first-run page to get started. The runtime is bundled and access is local to this computer. Configuration is available from Settings and the tray menu. Install FFmpeg separately; replace the entire program folder when updating. See [Windows testing guide](docs/TESTING_DESKTOP.md). macOS users currently follow the source installation steps below.

## Installation

Three steps, with no directories or configuration files to prepare in advance. Run from the repository root:

```powershell
& py -3.14 -m venv .venv                            # macOS: python3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .    # macOS: ./.venv/bin/python -m pip install -e ".[macos]"
& .\.venv\Scripts\peach.exe init                    # macOS: ./.venv/bin/peach init
```

Run without arguments, `peach init` asks five questions in the terminal; pressing Enter accepts the default shown in brackets:

| Question | Default |
| --- | --- |
| Data root (ledger, caches and the settings file live here) | `peach-data/` next to the repository |
| Local media directory (source `local`, must already exist) | `~\Videos` (`~/Movies` on macOS); required when that folder is missing |
| Listen scope: 1 = this machine only (127.0.0.1), 2 = LAN (0.0.0.0) | `1` |
| Service port | `8900` |
| LAN name (`<name>.local`, published only when listening on the LAN) | `peach` |

It then creates the data root, migrates the ledger to the latest schema, generates the local CA, writes
`<data root>/config.toml`, asks "scan <directory> now?" (default yes) to register that directory's files
in the ledger, and prints the next steps. The settings file declares only the one source you named; after
that `peach serve` starts the service and `peach scan local` rescans at any time. The listen address, port,
sources and replication switches are all edited in that settings file, explained item by item in
[`docs/OPERATIONS.md`](docs/OPERATIONS.md). The tray is started with `peach-tray`, without arguments.

You can answer in a browser instead of the terminal: skip step three and run `peach-tray` (or
double-click `Peach.exe` / `Peach.app`). Seeing that the machine is not configured yet, the tray starts a
setup service bound to `127.0.0.1` only and opens a browser on it. The page is the same five questions as a
form, plus a "scan now" checkbox that is ticked by default. On submit the tray stops the setup service,
switches to the normal Peach services, and runs the scan in the background if you asked for it. This path
calls the same logic as `peach init` and writes exactly the same files. While it waits, the tray menu reads
"等待完成首次设置" and its first item becomes "重新打开设置页".

To skip the questions, pass arguments: `peach init --no-input` (or any single option such as `--data-root`,
`--port` or `--mount local=/mnt/media`) generates the file from the built-in defaults plus your arguments;
the same path is taken when stdin is not a terminal. A file written this way carries three example sources,
`local = R:\media`, `115 = B:/` and `pikpak = A:/`, which must be changed to your own paths under
`[media.locations]` and `[media.mounts]`; leaving them means every source is offline, not an error.

Five facts:

- Listening on `127.0.0.1` needs no token. Reaching the service from a phone or any other device on the LAN (`--host 0.0.0.0`, and everything the tray starts) does: `peach init` has already written one to `<data root>/secrets/auth-token`, `peach token` prints it, and each device pastes it into the login page once. `peach serve` refuses to start when it binds a non-loopback address without a token, because that puts the whole collection and the write endpoints on the local network.
- Use `-e` for source development. Regular installations and wheels include pages and migrations and support running from any working directory.
- When the data root is not next to the repository, `peach serve` looks for it only via `PEACH_DATA_ROOT` and the `peach-data/` directories a few levels above the repository, so set `PEACH_DATA_ROOT` as well; the default data root needs no such step.
- Ledger paths are always in the Windows shape. On Windows the media directory goes straight into `[media.locations]`; on macOS the declared root is `R:\media` and the directory goes into `[media.mounts]`, where the local mount point does the translation. CloudDrive is not required — any cloud drive that mounts as a local path works; 115 and PikPak are recommendations, not requirements.
- The interface is currently available in Chinese only.

The service also starts without a settings file: `/healthz` reports `configured=false`, and the home page is the first-run form described above.

## Development

After initializing the virtual environment, run the tests with `& .\scripts\test.ps1` on Windows and `./scripts/test.sh` on macOS/Linux.
Each platform has exactly one official test entry point. The script locates the main project's virtual environment, forces the current worktree's `src` onto the import path and verifies the actual import location. The repository uses the standard-library `unittest`, not pytest.

During development, run the tests for the affected functional domain, for example
`& .\scripts\test.ps1 -Scope follow` on Windows and `./scripts/test.sh follow` on macOS/Linux.
The available domains are `follow`, `catalog`, `media`, `sync`, `metadata`, `tooling` and `web`; with
no argument the default `full` scope runs. `auto` picks domains from the changed files and falls back
to `full` when a file maps to none or touches migrations, shared test infrastructure or a dependency
manifest. Changes that span several domains, touch migrations, shared
test infrastructure or dependencies, prepare a release or have a large footprint must run the full
scope; a single local change does not need to rerun unrelated tests over and over.

## Dependency maintenance

The Python runtime and optional tools are all pinned to exact versions in `pyproject.toml`; the
self-hosted frontend packages are pinned jointly by `package.json`, `package-lock.json` and
`web/vendor/`. Optional dependencies stay out of the default runtime environment:

| extra | Consumer |
| --- | --- |
| `build` | PyInstaller packaging |
| `macos` | AppKit menu bar |
| `vision` | Face-framing scripts for avatars and covers |
| `maintenance-115` | 115 SHA-1 reconciliation script |

GitHub Dependabot checks Python, npm and GitHub Actions weekly; every update PR runs the official
tests on Windows and macOS with Python 3.12 and 3.14. After a frontend dependency update, first
install the locked packages:

```powershell
npm ci --ignore-scripts
```

Then rebuild the self-hosted files and source hashes from the locked packages:

```powershell
npm run vendor:web
```

Finally confirm that the pinned files in the repository match the manifest:

```powershell
npm run check:vendor
```

This Node tooling exists only to maintain the pinned frontend files; Peach pages still have no runtime build step and do not depend on a CDN.

Check the migration status and start a local development server:

```powershell
& .\.venv\Scripts\peach.exe migrate status
& .\.venv\Scripts\peach.exe serve --port 8900
```

The current entry points and limits of the production tray, the macOS menu bar, the local CA, mDNS and ledger replication are in [`docs/STATUS.md`](docs/STATUS.md) and [`docs/HANDOFF.md`](docs/HANDOFF.md). The README does not duplicate IPs, versions, port ownership or certificate state, all of which go stale quickly.

## Main pages

| Route | Purpose |
| --- | --- |
| `/` | Home |
| `/item/{id}` | Item details |
| `/performers` | Performer index |
| `/performers/{name}` | Performer profile |
| `/creators/{name}` | Creator profile and galleries |
| `/tags` | Tag management |
| `/immerse` | Immersive mode |
| `/playlists` | Playlists |
| `/follow` | Watch followed sources |
| `/follow-manage` | Manage followed sources and credential status |
| `/review` | Manual review |
| `/data-cleanup` | Data cleanup overview: junk files, duplicate files and empty folders |
| `/junk-files` | Junk file classification and decisions |
| `/trash` | Trash |
| `/stats` | Statistics, cloud-drive resource sync and orphaned-cache cleanup |
| `/taste` | Taste profile and browsing-history management |

`/healthz` provides side-effect-free health status, and `/api/sources` provides source reachability. Other API contracts are defined by the implementation and its tests; the README does not maintain the full set of endpoints, which drifts easily.

After deleting files by hand in a cloud-drive or local resource directory, open "Manage → Statistics → Resource sync" (`管理 → 统计 → 资源同步` in the interface) and scan for differences first. The scan runs in the background and shows progress per source; leaving the page does not interrupt it. Peach checks only mounted sources, and a directory that is temporarily unreadable is skipped rather than judged deleted. Missing entries go to the trash first, so recoverable ledger metadata is not lost immediately. Confirming the sync re-checks the candidates and cleans up screenshots, posters, image thumbnails, covers and playback caches that nothing in the regular collection still uses; candidate CSVs, source evidence, performer avatars and studio logos are never deleted as caches.

Promotional videos, advertisement images, URL shortcuts and other files bundled inside media packages go to "Manage → Data cleanup" (`管理 → 数据清理`, `/data-cleanup`). The junk-files page groups them into video, image, archive, audio, URL and other files; each entry can open its location on the cloud drive, be moved to the trash, or be marked "not junk" (`不是垃圾`) and undone under "Excluded" (`已排除`). Duplicate files share this management entry with junk files, and empty folders are cleaned up explicitly from a separate fieldset within it. Multi-select in the top bar batch-runs whichever decision or trash operations the current view offers. Peach lists candidates by file name, promotional directories and whatever duration or size evidence each type offers, and never permanently deletes on its own; after a physical file is permanently deleted from the trash, only parent directories inside the same source root that become empty as a result are removed with it — the source root itself is never deleted.

## Follow and candidates

Follow management accepts pasted links, names or IDs, and official creator pages on FANBOX, Patreon
and SubscribeStar can be registered directly. A checkbox per channel decides whether it takes part
in update checks; network access happens only during explicit lookups and update checks. Disabled
channels do not appear on the follow watch page and reappear once re-enabled. Service startup, health checks and ordinary browsing never go online.
When the F95zone site index has no match for a name, the results area offers a corresponding Google query; Google results are only for a person to verify the real thread link and never register a source automatically.

Rule34.xxx tag identities are case-insensitive. Cross-site sources are grouped by canonical author; `Collection(s)` in an F95 title is not part of the author name.
When an official homepage gives both a unique author name and a platform account, Peach learns that platform alias automatically; an existing manual decision is never overwritten.
A mere name similarity without an official identity chain only produces a suggestion, which is merged only after the user confirms; aliases can be removed at any time. Author avatars are taken preferentially from verified
official FANBOX/Pixiv pages, with archive sites as a fallback only. Connector design and evidence are in
[`ADR-0019`](docs/adr/0019-site-follow-connectors-and-variant-grouping.md).

Fetched updates stay in the `new` or `seen` candidate state. Only after an explicit save or approval in `/review` does the data enter the corresponding ledger truth or online assets.

## Documentation

- [`AGENTS.md`](AGENTS.md): the boundaries and skill index every change must follow.
- [`docs/STATUS.md`](docs/STATUS.md): current runtime state and verification results.
- [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md): open requirements and pending operations.
- [`docs/HANDOFF.md`](docs/HANDOFF.md): facts and working conventions that hold across tasks.
- [`docs/REUSE.md`](docs/REUSE.md): the reuse checklist to consult before adding or replacing an implementation.
- [`docs/adr/`](docs/adr/): architecture decisions, their reasons and trade-offs.

The documents above are currently available in Chinese only. [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md) each open with an English summary.

## License

Peach is released under AGPL-3.0-or-later; the full text is in [`LICENSE`](LICENSE). In practice this means: distributing a
modified version, or offering a modified version to others as a network service, requires publishing the source under the same license.

Copyright (C) 2026 longmeidao

The third-party frontend files pinned in the repository keep their upstream licenses; the files and source hashes are in
[`web/vendor/`](web/vendor/). FFmpeg is not distributed with the repository or the build output; users install it themselves and comply with its license.
