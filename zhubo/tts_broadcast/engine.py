from dataclasses import asdict, dataclass
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np


TONES = {
    "neutral": None,
    "warm": [0.45, 0, 0, 0, 0, 0, 0, 0.35],
    "energetic": [0.6, 0, 0, 0, 0, 0, 0.2, 0],
    "steady": [0, 0, 0, 0, 0, 0, 0, 0.8],
}


@dataclass(frozen=True)
class Parameters:
    speed: float = 1.0
    volume: float = 100.0
    tone: str = "neutral"
    intensity: float = 0.0

    def __post_init__(self):
        if not (0.5 <= self.speed <= 2 and 0 <= self.volume <= 200
                and 0 <= self.intensity <= 1 and self.tone in TONES):
            raise ValueError("参数超出范围")

    def values(self):
        vector = TONES[self.tone]
        return {**asdict(self), "duration_factor": 1 / self.speed,
                "emo_vector": None if vector is None else [v * self.intensity for v in vector]}


class Engine:
    """One model, used only by the broadcast synthesis worker."""

    def __init__(self, repo=Path("/home/ln/AI/index-tts"), threads=4):
        repo = Path(repo).resolve()
        self.voice = str(repo / "examples/voice_01.wav")
        sys.path.insert(0, str(repo))
        # Upstream normalizers and auxiliary weights resolve relative to its repo.
        os.chdir(repo)
        import torch
        from indextts.infer_v2_5 import IndexTTS2

        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        started = perf_counter()
        self.model = IndexTTS2(
            model_dir=str(repo / "checkpoints"),
            cfg_path=str(repo / "checkpoints/config.yaml"),
            use_bf16=True, use_cuda_kernel=False, use_qwen_emo=False,
        )
        self.info = {"initialization_s": perf_counter() - started,
                     "repo": str(repo), "gpu": torch.cuda.get_device_name(),
                     "torch": torch.__version__, "sample_rate": 22050,
                     "bf16": True, "num_beams": 1, "threads": threads}
        started = perf_counter()
        self.synthesize("欢迎来到直播间。", Parameters(), self.voice)
        self.info["warmup_s"] = perf_counter() - started

    def synthesize(self, text, parameters, voice):
        values = parameters.values()
        chunks = []
        for chunk in self.model.infer(
            spk_audio_prompt=voice, text=text, output_path=None, lang="ZH",
            stream_return=True, interval_silence=0, num_beams=1,
            max_text_tokens_per_segment=120, use_random=False,
            duration_factor=values["duration_factor"], emo_vector=values["emo_vector"],
        ):
            if not isinstance(chunk, list):
                pcm = chunk.numpy().reshape(-1).astype(np.int16)
                if pcm.size:
                    chunks.append(pcm)
        if not chunks:
            raise RuntimeError("模型未生成音频")
        return np.concatenate(chunks)
