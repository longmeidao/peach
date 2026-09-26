<p align="center">
  <img src="resources/peach-logo.png" alt="Peach" width="96">
</p>

<h1 align="center">Peach</h1>

<p align="center">A private video library for yourself: local drives, cloud drives and the creators you follow, all in one place.</p>

<p align="center">
  <a href="https://github.com/longmeidao/peach/releases">Download for Windows</a> ·
  <a href="https://github.com/longmeidao/peach/releases/tag/intro-video">Intro video</a> ·
  <a href="https://github.com/longmeidao/peach/issues">Report a problem</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="README.md">中文</a>
</p>

https://github.com/user-attachments/assets/40f7fb76-fece-4af9-86e1-e0279cc525af

> **18+** For adults managing their own adult-content collections. The repository contains no media or site data. When Peach connects to outside sites it uses your own accounts and access rights, and it does not get around paywalls, bot checks or other access controls.

- **Already-organized videos just work**: scanning reads the NFO files and posters that already sit next to your videos, so nothing needs to be scraped again.
- **Your files stay put**: scanning is read-only and files stay where they are. Renaming or moving only happens when you start it, with a preview first and an undo afterwards.
- **Cloud and local together**: once 115 or PikPak is mounted as a local drive with CloudDrive2, its videos join the same library as your hard drives.
- **Your data stays on your computer**: watch history, favorites and settings are stored locally. When filling in details, Peach only sends the video code to source sites.

## Screenshots

<table>
  <tr>
    <td><img src="https://github.com/longmeidao/peach/releases/download/intro-video/peach-home.jpg" alt="Home"></td>
    <td><img src="https://github.com/longmeidao/peach/releases/download/intro-video/peach-performer.jpg" alt="Performer page"></td>
  </tr>
  <tr>
    <td align="center">Home: filter by source, length and tags</td>
    <td align="center">Performer page: profile, aliases, links and every video</td>
  </tr>
  <tr>
    <td><img src="https://github.com/longmeidao/peach/releases/download/intro-video/peach-follow.jpg" alt="Following"></td>
    <td><img src="https://github.com/longmeidao/peach/releases/download/intro-video/peach-stats.jpg" alt="Statistics"></td>
  </tr>
  <tr>
    <td align="center">Following: one creator's updates from several sites in one feed</td>
    <td align="center">Statistics: where your videos live and how much you have watched</td>
  </tr>
</table>

## What it does

- **Search**: type a few characters and performers, codes and videos show up together.
- **Performer pages**: aliases, birthday and measurements, social accounts and JavDB and MISSAV links on one page, above every video of hers in your library and her photos. You can pick an avatar by drawing a box on any cover.
- **Filling in details**: by video code, Peach fills in titles, performers, studios and high-resolution covers from studio sites, DMM, JavBus, JavDB and others. It only fills empty fields and never overwrites your edits.
- **Playback**: play in the browser and pick up where you left off. Like, rate, save for later, add to a playlist, or "log a climax".
- **New releases**: turn on a subscription on a performer page and Peach checks for her new titles regularly. Creators can be followed across 11 sites such as FANBOX, Patreon and Kemono, and the same post on different sites shows up as one card.
- **Statistics**: which drive holds what, how much you have watched and which tags dominate, on one page.
- **Appearance**: light or dark, accent color and sidebar order are all yours to set.
- **Any screen**: works in the browser on desktop, tablet and phone.

## Download and use

### Windows

1. Download `Peach-<version>-windows-x64.zip` from [Releases](https://github.com/longmeidao/peach/releases), right-click it and choose "Extract All".
2. Double-click `Peach.exe`. Your browser opens the first-run setup page.
3. Pick your media folders and who may access Peach, then start the scan.

The test package is not code-signed yet. If Windows says "Windows protected your PC", make sure the file came from this project's Releases, then choose "More info → Run anyway". Transcoding and thumbnails need FFmpeg; without it you can still browse and play MP4 and WebM. See [Windows test build](docs/TESTING_DESKTOP.md) for how to install it.

### Run from source (Windows, macOS)

You need Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12 or newer (uv downloads a missing interpreter for you):

```powershell
git clone https://github.com/longmeidao/peach.git peach-app
cd peach-app
uv sync --locked --python 3.14
& .\.venv\Scripts\peach-tray.exe
```

On macOS, replace the last two lines with `uv sync --locked --python 3.14 --extra macos` and `./.venv/bin/peach-tray`.

LAN access, access passwords, updates and uninstalling are covered in [Operations](docs/OPERATIONS.md).

## FAQ

**Will it change my files?**
Scanning and filling in details never touch the original files. Only two things do: running an organize job you started (rename or move, with a preview and an undo for the last batch), and emptying the trash (which really deletes).

**I already organized my videos with another scraper. Can Peach use that?**
Peach reads the Kodi and Jellyfin layout: an `.nfo` named after the video and posters such as `<title>-poster.jpg`. Existing titles, performers, studios and posters show up right away.

**Which cloud drives are supported?**
115 and PikPak, mounted as local drives with CloudDrive2. Peach reads them like ordinary folders and does not store your cloud account.

**How do I watch on my phone?**
Choose "devices on the same network" during first-run setup, connect your phone to the same network and open the address shown on the setup page. Setting an access password is a good idea.

**Where is my data?**
In the `peach-data` folder on your computer. The Windows build keeps it in `%LOCALAPPDATA%\Peach\peach-data` by default.

## Reporting problems

Open an [issue](https://github.com/longmeidao/peach/issues) with the version, what you did, what you expected and what actually happened, ideally with a screenshot. Before taking screenshots, hide passwords, cookies, LAN addresses and full file paths, and do not upload database files or media. Report security issues privately as described in the [security policy](SECURITY.md).

## Documentation

Using Peach: [Windows test build](docs/TESTING_DESKTOP.md) · [Operations](docs/OPERATIONS.md) · [Sourcing](docs/SOURCING.md) · [Cloud drive mounts](docs/CLOUDDRIVE.md) · [Changelog](CHANGELOG.md)

Contributing: [Development guide](AGENTS.md) · [Architecture](docs/ARCHITECTURE.md) · [Testing and dependencies](docs/TESTING.md) · [Frontend](docs/FRONTEND.md) · [Reuse inventory](docs/REUSE.md) · [README maintenance](docs/README_MAINTENANCE.md). Verify changes with Windows `& .\scripts\test.ps1` or macOS/Linux `./scripts/test.sh`.

## Related projects

- [amane](https://github.com/sqzw-x/amane): Peach reaches studio sites and other sources through it.
- [Gfriends](https://github.com/gfriends/gfriends): performer avatar collection.
- [CloudDrive2](https://www.clouddrive2.com/): mounts cloud drives as local disks.
- [OpenAver](https://github.com/slive777/OpenAver), [Javinizer-Go](https://github.com/javinizer/javinizer-go), [MetaTube](https://github.com/metatube-community/metatube-sdk-go), [MDCx](https://github.com/sqzw-x/mdcx): Peach learned from their source parsing and recommendation approaches.

The full reuse and credits list is in the [reuse inventory](docs/REUSE.md).

## License

[AGPL-3.0-or-later](LICENSE) · Copyright (C) 2026 longmeidao. Bundled third-party frontend files keep their own licenses; see [web/vendor](web/vendor/).
