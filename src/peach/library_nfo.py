"""Kodi/Jellyfin 影片及单集 NFO 的本地边车适配。"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from .catalog_rules import release_code_from_text
from .scan import VIDEO


def sidecars(video: Path):
    files = {path.name.casefold(): path for path in video.parent.iterdir() if path.is_file()}
    single = sum(path.suffix.lower() in VIDEO for path in files.values()) == 1
    nfo = files.get((video.stem + '.nfo').casefold())
    if nfo is None and single:
        nfo = files.get('movie.nfo')
    names = [video.stem + '-poster', video.stem]
    if single:
        names.extend(['poster', 'folder', 'cover'])
    posters = [files[name.casefold() + extension] for name in names
               for extension in ('.jpg', '.jpeg', '.png', '.tbn')
               if name.casefold() + extension in files]
    return nfo, posters


def read_nfo(path: Path):
    """保留完整原文；拒绝 DTD，并限制 XML 的输入体积。"""
    with path.open('rb') as handle:
        raw = handle.read(1024 * 1024 + 1)
    # XML 的 UTF-16/32 编码包含零字节；声明检查同样覆盖这些编码。
    declarations = raw.replace(b'\x00', b'').upper()
    if len(raw) > 1024 * 1024 or b'<!DOCTYPE' in declarations or b'<!ENTITY' in declarations:
        raise ValueError('NFO 文件过大或包含实体声明')
    root = ET.fromstring(raw)
    if root.tag not in {'movie', 'episodedetails', 'musicvideo'}:
        raise ValueError('NFO 不是影片或单集资料')
    def text(*keys):
        return next(((root.findtext(key) or '').strip() for key in keys
                     if (root.findtext(key) or '').strip()), '')
    identifiers = [node.text for node in root.findall('uniqueid')
                   if node.get('type', '').lower() in {'javboss', 'jav', 'javid', 'dvdid', 'num'}]
    identifiers.extend([text('num'), text('sorttitle')])
    # 通用 id 常是 IMDb/TMDb；仅明确的番号形状参与 JAV 身份识别。
    for value in [text('id'), *(node.text or '' for node in root.findall('uniqueid'))]:
        if re.fullmatch(r'(?:[A-Za-z]{2,12}[-_]\d{2,8}|FC2[-_](?:PPV[-_])?\d+)', value.strip(), re.I):
            identifiers.append(value)
    codes = {code for value in identifiers if (code := release_code_from_text(value or ''))}
    if len(codes) > 1:
        raise ValueError('NFO 包含多个不同番号')
    genres = list(dict.fromkeys(node.text.strip() for key in ('genre', 'tag')
                  for node in root.findall(key) if node.text and node.text.strip()))
    payload = dict(id=next(iter(codes), ''), title=text('title', 'localtitle', 'name'),
        original_title=text('originaltitle'), maker=text('studio'),
        series=text('set/name', 'set', 'showtitle'),
        release_date=text('premiered', 'releasedate', 'aired'),
        director=text('director'), runtime=text('runtime'),
        actresses=[{'japanese_name': (node.findtext('name') or '').strip()}
                   for node in root.findall('actor')], genres=genres, local_tags=genres,
        nfo_kind=root.tag, source_generator=text('generator'),
        local_art=text('art/poster', 'thumb[@aspect="poster"]', 'thumb'))
    return payload, raw


def local_art(video: Path, payload: dict):
    """仅读取影片所在目录内的本地图片，远端引用保留在原文。"""
    value = payload.get('local_art', '')
    if not value or '://' in value:
        return None
    path = (video.parent / value).resolve()
    if path.is_relative_to(video.parent.resolve()) and path.is_file():
        return path
    return None
