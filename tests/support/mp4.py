"""测试用的最小 MP4：只有时间表，没有真实媒体数据。

`peach.mp4index` 只读 `moov`，关键帧表、时长表和显示时间偏移表都能这样造出来，
用例因此不必依赖 FFmpeg 或真实片源。
"""
from __future__ import annotations

import struct


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def minimal_mp4(
    *,
    timescale: int,
    sample_delta: int,
    samples: int,
    keyframe_every: int,
    composition_offsets: bool = False,
) -> bytes:
    """够 `peach.mp4index` 解析关键帧的最小 MP4。

    `composition_offsets` 决定视频轨里有没有 `ctts`。有 B 帧的片源缺了这张表，容器
    声明的显示时刻就是解码顺序，浏览器会把倒着走的帧全丢掉。
    """
    mdhd = box(b"mdhd", struct.pack(">4sIIII HH", bytes(4), 0, 0, timescale,
                                    samples * sample_delta, 0, 0))
    hdlr = box(b"hdlr", struct.pack(">4sI4s", bytes(4), 0, b"vide") + bytes(12))
    stts = box(b"stts", struct.pack(">IIII", 0, 1, samples, sample_delta))
    sync = [n for n in range(1, samples + 1) if (n - 1) % keyframe_every == 0]
    stss = box(b"stss", struct.pack(">II", 0, len(sync))
               + b"".join(struct.pack(">I", n) for n in sync))
    ctts = (box(b"ctts", struct.pack(">IIII", 0, 1, samples, sample_delta))
            if composition_offsets else b"")
    stbl = box(b"stbl", stts + stss + ctts)
    mdia = box(b"mdia", mdhd + hdlr + box(b"minf", stbl))
    return (box(b"ftyp", b"isom" + bytes(8))
            + box(b"moov", box(b"trak", mdia))
            + box(b"mdat", bytes(64)))
