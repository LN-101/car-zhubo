"""Check the IndexTTS-2.5 migration wiring without touching the live services.

Verifies:
  * the reported engine version is the real one (not a hardcoded 2.5 label)
  * language selection uses codes the official tokenizer actually knows
  * the GPT-style speed_factor maps onto IndexTTS duration_factor
  * the in-repo HTTP wrapper and the backend adapter agree on both

Run:  .venv\\Scripts\\python.exe scripts/verify_indextts25_switch.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# The Windows console defaults to GBK here, which cannot encode the Spanish and
# Arabic samples used below.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from app.config import settings  # noqa: E402
from app.tts_idextts2 import (  # noqa: E402
    IndexTTS2Engine,
    index_tts2_label,
    normalize_index_tts2_version,
)

# The official tokenizer's LANGUAGE_DICT keys; a code outside this set silently
# falls back to "common" instead of raising, so it must never be emitted.
OFFICIAL_LANGUAGE_CODES = {
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca",
    "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms",
    "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la",
    "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn",
    "et", "mk", "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
    "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc", "ka", "be",
    "tg", "sd", "gu", "am", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha",
    "ba", "jw", "su", "yue", "minnan", "wuyu", "dialect", "zh/en", "en/zh",
    "common",
}

failures: list[str] = []


def check(label: str, actual, expected) -> None:
    ok = actual == expected
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {actual!r}" + ("" if ok else f" (expected {expected!r})"))
    if not ok:
        failures.append(label)


def load_wrapper():
    path = ROOT / "scripts" / "index_tts2_server.py"
    spec = importlib.util.spec_from_file_location("index_tts2_wrapper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("1. version normalisation")
    check("normalize(None)", normalize_index_tts2_version(None), None)
    check("normalize('')", normalize_index_tts2_version(""), None)
    check("normalize('2')", normalize_index_tts2_version("2"), "2.0")
    check("normalize(2.0)", normalize_index_tts2_version(2.0), "2.0")
    check("normalize('2.5')", normalize_index_tts2_version("2.5"), "2.5")
    check("normalize(2.5)", normalize_index_tts2_version(2.5), "2.5")
    check("label('2.0')", index_tts2_label("2.0"), "IndexTTS-2.0")
    check("label('2.5')", index_tts2_label("2.5"), "IndexTTS-2.5")
    check("label(None)", index_tts2_label(None), "IndexTTS")

    adapter = IndexTTS2Engine(settings)
    wrapper = load_wrapper()

    print("\n2. language codes (must exist in the official LANGUAGE_DICT)")
    cases = [
        ("欢迎来到汽车直播间，今天介绍这款车型。", "ZH"),
        ("こんにちは、今日はいい天気ですね。", "JA"),
        ("Hello, welcome to the live stream.", "EN"),
        ("¿Cómo estás? El coche es muy rápido.", "ES"),
        ("مرحبا بكم في غرفة البث المباشر", "AR"),
    ]
    for text, expected in cases:
        for name, fn in (("adapter", adapter._language_for_text), ("wrapper", wrapper.IndexTTS2Server._language_for_text)):
            code = fn(text)
            check(f"{name} {expected} <- {text[:14]}", code, expected)
            if code.lower() not in OFFICIAL_LANGUAGE_CODES:
                failures.append(f"{name} emitted unknown code {code!r}")
                print(f"  FAIL  {name} emitted {code!r}, which is not an official tokenizer key")

    print("\n3. speed_factor -> duration_factor (larger duration = slower)")
    check("speed 1.0", round(IndexTTS2Engine._duration_factor(1.0), 4), 1.0)
    check("speed 1.4", round(IndexTTS2Engine._duration_factor(1.4), 4), round(1 / 1.4, 4))
    check("speed 0.7", round(IndexTTS2Engine._duration_factor(0.7), 4), round(1 / 0.7, 4))
    check("speed 2.0 clamps", round(IndexTTS2Engine._duration_factor(2.0), 4), round(1 / 1.6, 4))
    check("speed 0.1 clamps", round(IndexTTS2Engine._duration_factor(0.1), 4), round(1 / 0.6, 4))
    check("speed None", IndexTTS2Engine._duration_factor(None), 1.0)

    print("\n4. live engine status (the running HTTP wrapper)")
    status = adapter.status()
    for key in ("provider", "label", "model_version", "speed_control_supported", "configured", "reachable", "ready", "mode", "endpoint"):
        print(f"  {key:24} = {status.get(key)!r}")
    local_version = adapter._local_version()
    print(f"  {'local checkpoint version':24} = {local_version!r}")
    remote = status["model_version"]
    if remote == "2.5":
        print("  PASS  engine serves 2.5 and speed control is available")
    else:
        print(f"  NOTE  engine serves {remote!r}; speed control reported as {status['speed_control_supported']!r}")

    print()
    if failures:
        print(f"FAILED {len(failures)} check(s): " + ", ".join(failures))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
