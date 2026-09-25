<p align="center">
  <img src="resources/peach-logo.png" alt="Peach" width="96">
</p>

<h1 align="center">Peach</h1>

<p align="center">Turn media on disks, mounted drives and followed sources into a private library of your own.</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/releases">Download the Windows test package</a> ·
  <a href="#feature-preview">Feature preview</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="README.md">中文</a>
</p>

Peach is a single-user, local-first media library. It brings search, playback, organization and followed updates into one browser interface, while the catalog, watch history and review decisions stay in a local SQLite ledger.

> **18+** Intended for adults managing adult-content collections. The repository contains no media or site datasets. Source connectors require the user's own access rights and do not bypass paywalls, bot checks or other access controls.

## Feature preview

https://github.com/user-attachments/assets/a97049bd-ddaf-4844-99ca-b18e97957d2a

<p align="center"><a href="docs/assets/peach-overview.mp4">Download the 58-second feature video</a></p>

## What it does

<table>
  <thead>
    <tr>
      <th width="180" nowrap>Capability</th>
      <th>Summary</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="180" nowrap><strong>Visual library</strong></td>
      <td>Browse videos and photo collections by cover; search by work, performer, studio, creator, series or tag; use library filters, identity completion and large-cover mode from the same page.</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>Playback and links</strong></td>
      <td>Play media from local disks and mounted drives, with people, studios, tags and related works beside the player; keep watch-later items, viewing state, Mixes, playlists and a corner miniplayer.</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>People and identity</strong></td>
      <td>Collect portraits, aliases, external links and work relationships on performer profiles, while external identity candidates retain provenance and wait for review.</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>Collection and enrichment</strong></td>
      <td>Scan folders for NFO files, local posters and existing metadata; fetch missing covers, portraits and metadata, then write reviewed results to the library. Turn on push discovery and new files reach the library within seconds — local folders through filesystem events, cloud mounts through CloudDrive2 notifications — and periodic scans pick up any file the push missed.</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>Multi-source following</strong></td>
      <td>Register official or archive sources, see one creator's updates across sites and save content inside Peach.</td>
    </tr>
    <tr>
      <td width="180" nowrap><strong>Interface and devices</strong></td>
      <td>Use light or dark themes, custom colors and responsive pages on desktop, tablet and phone; review duplicates, unavailable files, trash and external candidates in one place.</td>
    </tr>
  </tbody>
</table>

## Get Peach

The standalone Windows x64 test package is available from [GitHub Releases](https://github.com/longmeidao/peach/releases); Windows and macOS can also run Peach from source, which requires Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12 or newer. See [Windows testing](docs/TESTING_DESKTOP.md) and [operations](docs/OPERATIONS.md) for downloads, verification and configuration.

Running from source (the example uses Python 3.14; uv downloads a missing interpreter):

```powershell
git clone https://github.com/longmeidao/peach.git peach-app
cd peach-app
uv sync --locked --python 3.14
& .\.venv\Scripts\peach-tray.exe
```

On macOS replace the last two commands with `uv sync --locked --python 3.14 --extra macos` and `./.venv/bin/peach-tray`. The tray opens the first-run setup page, where you pick media folders, access scope and port.

FFmpeg and ffprobe are installed separately: without them you can still browse and play browser-compatible formats, while transcoding, probing and thumbnails stay unavailable. Source deployments keep data in `peach-data/` next to the repository, the standalone package uses `%LOCALAPPDATA%\Peach\peach-data`, and `PEACH_DATA_ROOT` points either one elsewhere. LAN and HTTPS access are covered in [operations](docs/OPERATIONS.md); updates and uninstall live under Manage → Configuration → Updates and maintenance, with the standalone steps in [Windows testing](docs/TESTING_DESKTOP.md).

## Data boundaries

Media stays in its original folders by default; organizing is an explicit action you start yourself, with a preview first and a rollback afterwards. The catalog, identities, viewing history and human decisions stay in a local SQLite ledger. External metadata and AI output enter as candidates with provenance and confidence; credentials stay outside Git, logs and API responses. Peach is for single-user self-hosting and does not provide a public-site or team permission model.

Each release ships a seed of entity facts: aliases, site identifiers, official and social links, profiles, agency memberships and label-to-maker relations for performers, studios and agencies, with no images. After a scan it only fills blanks on entities already in your ledger; the only rows it replaces are the ones an older seed wrote itself. Anything that disagrees with a human decision goes to a review file, and every batch can be reverted.

## Documentation

Using Peach: [Windows testing](docs/TESTING_DESKTOP.md) · [Operations](docs/OPERATIONS.md) · [Sources](docs/SOURCING.md) · [Project status](docs/STATUS.md) · [Changelog](CHANGELOG.md) · [Security policy](SECURITY.md)

Developing Peach: [Development agreement](AGENTS.md) · [Architecture](docs/ARCHITECTURE.md) · [Testing and dependencies](docs/TESTING.md) · [Frontend](docs/FRONTEND.md) · [Product backlog](docs/PRODUCT_BACKLOG.md) · [Handover notes](docs/HANDOFF.md) · [Reuse list](docs/REUSE.md) · [README maintenance](docs/README_MAINTENANCE.md) · [Architecture decisions](docs/adr/)

Run development checks through `& .\scripts\test.ps1` on Windows or `./scripts/test.sh` on macOS/Linux. File issues with the version, the steps, and the expected and actual results; never attach a real ledger, media, cookies or private keys. Report security problems through the [security policy](SECURITY.md).

## License

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao.

Vendored frontend files retain their upstream licenses and provenance under [web/vendor](web/vendor/).
