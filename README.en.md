<p align="center">
  <img src="resources/peach-logo.png" alt="Peach" width="96">
</p>

<h1 align="center">Peach</h1>

<p align="center">A personal library for media across your disks, mounted drives and followed sources.</p>

The home page includes videos without thumbnails. Search suggestions come from the current library. An empty library keeps the people, studio and tag layout and offers actions to add content or sources.

<p align="center">
  <a href="https://github.com/longmeidao/peach/releases">Download for Windows</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="README.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/longmeidao/peach/test.yml?branch=master&amp;label=tests&amp;style=flat" alt="Tests"></a>
  <a href="https://github.com/longmeidao/peach/releases"><img src="https://img.shields.io/github/v/release/longmeidao/peach?include_prereleases&amp;label=release&amp;style=flat" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue?style=flat" alt="AGPL-3.0-or-later"></a>
</p>

Peach is a single-user, local-first media system. Search, play and organize media you already own on your computer, with browser access from your phone over the LAN. Your library, viewing history and review decisions stay in a local SQLite ledger.

> **18+** Intended for adults managing adult-content collections. The repository contains no media or site datasets; documentation uses SFW demo material only. Connectors require access rights and do not bypass paywalls, bot verification or other access controls.

## Features

| Capability | What it does |
| --- | --- |
| Browse and search | Find videos and photo collections by work, performer, studio, creator, series or tag |
| Play and save | Play local and mounted media; keep watch-later items, viewing state, Mixes and playlists |
| Follow updates | Register official or archive sources, explicitly check updates, view and save content inside Peach |
| Review and organize | Review external candidates; manage duplicates, junk, unavailable files and trash |
| Taste and history | Explore your taste profile and manage browsing records and reasons for liking items |

CloudDrive · 115 and CloudDrive · PikPak connect through mounted local folders. Sign in and mount them in CloudDrive first, then add the folders to Peach. Local disks alone also work.

First-run setup offers an optional browser-history import guide. Completed imports hide the guide; Skip remembers dismissal in the current browser, while collapsing keeps it available. The Taste page retains its read and import buttons. SFW mode blurs, desaturates and dims images and videos and stops hover previews; text remains visible. Cloud reconciliation appears only when a cloud source is configured; empty-folder cleanup also supports local disks.

Tray-managed services let you adjust media sources under Manage → Configuration on the host computer, including through its LAN hostname. Setup and configuration provide download links when dependencies are not detected, with mount drivers shown for the host operating system.

Follow sources include FANBOX, Patreon, SubscribeStar, Kemono, Pawchive, Coomer, the Rule34 family and F95zone. Availability depends on the site and your access rights. See [source collection](docs/SOURCING.md) for supported workflows and boundaries.

## Quick start

Settings control whether local and followed videos play automatically when their details open.

Portraits and brand marks allow moderate enlargement in large and compact views. Very small images use their native size with a blurred background. Display areas below 64 px retain the regular icon treatment.

Settings offers a default JAV cover choice: official covers or preview images across the home feed, continue watching, Mix, video cards and playback queues. Missing images fall back to the other type. The default JAV cover size can be large or small; both use the selected cover type. Preferences are saved in the current browser.

Peach is **pre-1.0**. The application interface is currently Chinese only.

| Platform | Available today |
| --- | --- |
| Windows | Standalone test package or source installation |
| macOS | Source installation; standalone desktop packaging is in development |
| Linux | Unsupported and untested |

### Windows test package

1. Download `Peach-<version>-windows-x64.zip` from [GitHub Releases](https://github.com/longmeidao/peach/releases) and extract the complete archive.
2. Open `Peach.exe`, select existing media folders in the setup page and submit.
3. Browse your library. Media and service configuration are available from page settings or the tray menu.

The test package is accessible only on the same computer and needs no Python, Git, Node or OpenSSL.
Data lives separately from the program in `%LOCALAPPDATA%\Peach\peach-data`. To update, exit the tray, extract the complete new package and keep the data directory.

Install FFmpeg and ffprobe separately for transcoding, probing and thumbnails. Without them, browsing and playback of browser-compatible formats remain available.
The package is unsigned; see [Windows testing](docs/TESTING_DESKTOP.md) for download verification, configuration and feedback.

### Run from source

Requires Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) **0.12.10** and **Python 3.12 or newer**. These examples use 3.14; uv can download a missing Python interpreter. CI covers 3.12 and 3.14.
Node is unnecessary at runtime; frontend development needs Node 24 or newer.

Clone the repository:

```shell
git clone https://github.com/longmeidao/peach.git peach-app
cd peach-app
```

Windows: create the environment, install and launch setup in PowerShell:

```powershell
uv sync --locked --python 3.14
& .\.venv\Scripts\peach-tray.exe
```

macOS: create the environment, install menu-bar support and launch setup:

```shell
uv sync --locked --python 3.14 --extra macos
./.venv/bin/peach-tray
```

Setup configures media folders, access scope and ports. Alternatively, use the `peach init` terminal wizard followed by `peach serve`; executables are in the virtual environment directories above.

Source deployments default to a sibling `peach-data/` directory. Set `PEACH_DATA_ROOT` for a custom location.
The access password is optional during setup. Leave it blank to allow devices that can reach Peach to enter directly. Configuration lets you set, change or disable the password; the login page offers session durations. Existing deployments retain their current login requirement. Local CA generation requires OpenSSL.
See [operations](docs/OPERATIONS.md) for configuration, HTTPS, CloudDrive mounts and non-interactive initialization.

## Your data

- Media stays in its original folders. Transcoding uses disposable derived caches without rewriting source files.
- The SQLite ledger stores library identities, viewing behavior and human decisions. External metadata and AI assertions retain provenance and confidence and require review to become truth.
- Credentials live in the data directory's `secrets/`, outside Git, logs and API responses. Migrations and irreversible operations require a backup and authorization.
- Each deployment serves one person and is not intended for teams or public hosting.
- Optional replication is off by default. The verified setup is a Windows writer and macOS reader, each with a local ledger. A shared folder transports data; replication and takeover are explicit. Divergence makes the ledger read-only rather than automatically merging it. See [replication boundaries](docs/adr/0017-dual-host-local-runtime-and-sync-boundaries.md).

The repository distributes no media, covers, thumbnails, metadata or site datasets. External titles, images and descriptions remain the content and copyright of their respective sites and creators.

## Development and contributions

The backend is a FastAPI modular monolith with SQLite as the truth store. The frontend migrates page by page to Vite, TypeScript and Preact islands.
Python serves existing pages and committed build output from `web/`; runtime requires neither Node nor a CDN.

| Path | Contents |
| --- | --- |
| `src/peach/` | API, media, ledger and source adapters |
| `frontend/` | TypeScript, Preact islands and Vite build |
| `web/` | Pages, styles, self-hosted dependencies and `web/dist/` output |
| `migrations/` | Versioned SQLite migrations |
| `scripts/`, `tests/` | Development entry points, maintenance scripts and isolated tests |
| `docs/` | Guides, architecture and project status |

Read the [working agreement](AGENTS.md) before changing the project. Tests use temporary databases and media. Run the official entry point in an isolated worktree.

Windows: run checks for the current changes:

```powershell
& .\scripts\test.ps1
```

macOS: run checks for the current changes:

```shell
./scripts/test.sh
```

The default `auto` scope selects affected domains. See [testing and dependencies](docs/TESTING.md) for the CI policy.
See [frontend development](docs/FRONTEND.md) for installation, builds, type checking and committed output.
Dependency manifests and lockfiles define versions; Dependabot checks Python, npm and GitHub Actions weekly.

For issues, include the version, steps, expected result and actual result. Do not attach a real ledger, media, cookies or private keys.
Report security issues according to the [security policy](SECURITY.md).

## Documentation

Detailed project documentation is in Chinese.

| Task | Guide |
| --- | --- |
| Download, configure and test the package | [Windows testing](docs/TESTING_DESKTOP.md) |
| Configure media, LAN, HTTPS and replication | [Operations](docs/OPERATIONS.md) |
| Understand collection and evidence boundaries | [Sources](docs/SOURCING.md) |
| Check the installed runtime and verification | [Status](docs/STATUS.md) |
| Find open work | [Backlog](docs/PRODUCT_BACKLOG.md) |
| Change and maintain Peach | [Working agreement](AGENTS.md) · [Frontend](docs/FRONTEND.md) · [Reuse](docs/REUSE.md) |
| Read durable conventions and architecture | [Handoff](docs/HANDOFF.md) · [Decisions](docs/adr/) |

README describes mainline capabilities. Status records the installed runtime and its verification; Releases identifies distributed packages.
See [README maintenance](docs/README_MAINTENANCE.md) for the documentation update process.

## License

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao.

Vendored frontend dependencies retain upstream licenses and provenance in [web/vendor](web/vendor/).
FFmpeg is not distributed with the repository or packages; install it separately and follow its license.
