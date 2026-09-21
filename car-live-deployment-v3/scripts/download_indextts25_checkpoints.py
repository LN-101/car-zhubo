"""Download the official IndexTTS-2.5 checkpoint files.

Why this does not use `modelscope.hub.file_download`: that helper stages the
payload in a location that is not observable from this sandboxed shell, which
made progress impossible to verify. This script streams straight to the
destination with an explicit HTTP Range resume, so every byte is accounted for.

ModelScope is used because hf-mirror measured ~0.05 MB/s from this host while
ModelScope sustained ~5.8 MB/s.

Usage:
    python scripts/download_indextts25_checkpoints.py [--dest DIR]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

MODEL_ID = "IndexTeam/IndexTTS-2.5"
MIRROR = f"https://modelscope.cn/models/{MODEL_ID}/resolve/master"

# Exact byte sizes published by the official IndexTTS-2.5 model repository.
EXPECTED = {
    "config.yaml": 2860,
    "gpt.pth": 3259599833,
    "s2mel.pth": 414908601,
    "codec.pth": 607290935,
    "wav2vec2bert_stats.pt": 9343,
    "feat1.pt": 57170,
    "feat2.pt": 374866,
    "multilingual_zh_ja_yue_char_del.tiktoken": 907395,
}

CHUNK = 1024 * 1024


def download(name: str, size: int, dest_dir: Path) -> str:
    destination = dest_dir / name
    if destination.is_file() and destination.stat().st_size == size:
        return "skip"

    partial = dest_dir / (name + ".part")
    have = partial.stat().st_size if partial.is_file() else 0
    if have > size:
        have = 0

    headers = {"Range": f"bytes={have}-"} if have else {}
    timeout = httpx.Timeout(30.0, read=120.0, write=60.0, pool=30.0)
    with httpx.Client(timeout=timeout, follow_redirects=True, trust_env=False) as client:
        with client.stream("GET", f"{MIRROR}/{name}", headers=headers) as response:
            if response.status_code not in (200, 206):
                raise RuntimeError(f"HTTP {response.status_code}")
            if have and response.status_code != 206:
                # The mirror ignored the range request; start over.
                have = 0
            mode = "ab" if have else "wb"
            written = have
            reported = 0
            started = time.perf_counter()
            with open(partial, mode) as stream:
                for chunk in response.iter_bytes(CHUNK):
                    stream.write(chunk)
                    written += len(chunk)
                    # One compact progress line roughly every 10% of the file.
                    step = max(size // 10, 1)
                    if written - reported >= step or written >= size:
                        reported = written
                        elapsed = max(time.perf_counter() - started, 1e-6)
                        rate = (written - have) / elapsed / 1024 / 1024
                        print(
                            f"    {name}: {written / 1024 / 1024:8.1f} / {size / 1024 / 1024:.1f} MB"
                            f"  ({rate:.1f} MB/s)",
                            flush=True,
                        )

    actual = partial.stat().st_size
    if actual != size:
        raise RuntimeError(f"size mismatch: got {actual}, expected {size}")
    os.replace(partial, destination)
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest",
        default=str(Path(__file__).resolve().parents[1] / ".downloads" / "indextts25"),
        help="destination directory for the checkpoint files",
    )
    args = parser.parse_args()
    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    total = sum(EXPECTED.values())
    print(f"source : {MIRROR}", flush=True)
    print(f"dest   : {dest_dir}", flush=True)
    print(f"total  : {total / 1024 / 1024 / 1024:.2f} GB", flush=True)

    failures: list[str] = []
    started = time.perf_counter()
    for name, size in EXPECTED.items():
        try:
            state = download(name, size, dest_dir)
            print(f"[{state:>4}] {name} ({size / 1024 / 1024:.1f} MB)", flush=True)
        except Exception as exc:  # noqa: BLE001
            failures.append(name)
            print(f"[fail] {name}: {type(exc).__name__}: {str(exc)[:300]}", flush=True)

    complete = sum(1 for n, s in EXPECTED.items() if (dest_dir / n).is_file() and (dest_dir / n).stat().st_size == s)
    print(f"--- {complete}/{len(EXPECTED)} complete in {time.perf_counter() - started:.0f}s ---", flush=True)
    if failures:
        print("FAILED: " + ", ".join(failures), flush=True)
        return 1
    print("ALL OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
