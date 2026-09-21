import argparse
import json
import os
from pathlib import Path
import platform
import re
import sys
from time import perf_counter

import numpy as np
import soundfile as sf

from .playback import Player, Segment


def split_script(text, first_limit=16, limit=32):
    # Length targets group complete phrases; never slice inside a spoken phrase.
    # Decimal dots stay inside phrases; punctuation remains attached to speech.
    phrases = re.findall(r".+?(?:[。！？!?；;，,\n]+|(?<!\d)\.(?!\d)|$)", text, re.S)
    segments = []
    pending = ""
    for phrase in phrases:
        phrase = phrase.strip()
        if not phrase:
            continue
        target = first_limit if len(segments) < 2 else limit
        if pending and len(pending) + len(phrase) > target:
            segments.append(pending)
            pending = ""
        pending += phrase
    if pending:
        segments.append(pending)
    return segments


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("/home/ln/AI/index-tts"))
    parser.add_argument("--voice", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/broadcast"))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args()
    text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    segments = split_script(text)
    if not segments:
        parser.error("script is empty")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    repo = args.repo.resolve()
    voice = args.voice.resolve() if args.voice else repo / "examples/voice_01.wav"
    sys.path.insert(0, str(repo))
    # Upstream normalizers and auxiliary weights use repository-relative paths.
    os.chdir(repo)
    import torch
    import sounddevice as sd
    from indextts.infer_v2_5 import IndexTTS2

    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    started = perf_counter()
    model = IndexTTS2(
        model_dir=str(repo / "checkpoints"),
        cfg_path=str(repo / "checkpoints/config.yaml"),
        use_bf16=True,
        use_cuda_kernel=False,
        use_torch_compile=args.compile,
    )
    initialization = perf_counter() - started

    def synthesize(sentence):
        for chunk in model.infer(
            spk_audio_prompt=str(voice), text=sentence, output_path=None,
            lang="ZH", stream_return=True, interval_silence=0,
            max_text_tokens_per_segment=120, num_beams=1,
        ):
            if isinstance(chunk, list):
                continue  # Upstream emits an empty silence list when interval_silence=0.
            pcm = chunk.numpy().reshape(-1).astype(np.int16)
            if pcm.size:
                yield pcm

    started = perf_counter()
    list(synthesize("欢迎来到直播间。"))
    warmup = perf_counter() - started
    report = {
        "environment": {
            "gpu": torch.cuda.get_device_name(), "torch": torch.__version__,
            "python": platform.python_version(), "repo": str(repo),
            "voice": str(voice), "sample_rate": 22050,
            "bf16": True, "num_beams": 1, "threads": args.threads,
            "compile": args.compile,
            "device": sd.query_devices(kind="output")["name"],
        },
        "initialization_s": initialization, "warmup_s": warmup,
        "measurement": "Warm request; first output uses PortAudio DAC timestamps, not acoustic capture.",
        "script": text, "segments": segments, "runs": [],
    }
    for run in range(args.runs):
        player = Player()
        audio = []
        timings = []
        first_pcm = None
        inference_s = 0.0
        started = perf_counter()
        try:
            with player.open():
                for index, sentence in enumerate(segments):
                    if player.cancelled.is_set():
                        break
                    segment_started = perf_counter()
                    queue_wait = 0.0
                    for pcm in synthesize(sentence):
                        ready = perf_counter()
                        if first_pcm is None:
                            first_pcm = ready - started
                        audio.append(pcm)
                        wait_started = perf_counter()
                        player.put(Segment(len(audio) - 1, sentence, pcm))
                        queue_wait += perf_counter() - wait_started
                    elapsed = perf_counter() - segment_started - queue_wait
                    inference_s += elapsed
                    timings.append({"id": index, "text": sentence, "inference_s": elapsed,
                                    "queue_wait_s": queue_wait})
                synthesis_done = perf_counter() - started
                player.finish()
                player.finished.wait()
        except KeyboardInterrupt:
            player.cancel()
            print("Cancelled.")
            return
        wav = np.concatenate(audio)
        sf.write(output / f"run-{run + 1}.wav", wav, 22050, subtype="PCM_16")
        duration = len(wav) / 22050
        first_output = player.first_output_at - started
        metrics = {
            "first_pcm_s": first_pcm, "first_device_output_s": first_output,
            "first_output_within_3s": first_output <= 3,
            "synthesis_wall_s": synthesis_done, "audio_s": duration,
            "rtf": inference_s / duration,
            "playback_s": player.last_output_at - player.first_output_at,
            "streamed_before_synthesis_done": first_output < synthesis_done,
            "underrun_events": player.underrun_events,
            "underrun_s": player.underrun_frames / 22050,
            "device_underflows": player.device_underflows,
            "played_ids": player.played_ids, "segments": timings,
        }
        report["runs"].append(metrics)
        (output / "metrics.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Report: {output / 'metrics.json'}")


if __name__ == "__main__":
    main()
