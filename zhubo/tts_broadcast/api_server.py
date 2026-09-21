"""
FastAPI server for Zhubo TTS service.
Provides REST API endpoints for speech synthesis.
"""
import argparse
import base64
import binascii
import io
import logging
import tempfile
import threading
import wave
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn

from .engine import Engine, Parameters


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000, description="Text to synthesize")
    reference_audio_base64: Optional[str] = Field(default=None, max_length=8 * 1024 * 1024)
    speaker: str = Field(default="default", description="Speaker/voice reference")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed factor")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Volume level")
    tone: str = Field(default="neutral", description="Tone/emotion: neutral, warm, energetic, steady")
    intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Tone intensity")


class TTSService:
    def __init__(self, repo_path: Path, voice_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path).resolve()
        self.inference_lock = threading.Lock()
        self.voice_dir = Path(voice_dir) if voice_dir else self.repo_path / "examples"
        
        logger.info(f"Initializing TTS engine from {self.repo_path}")
        self.engine = Engine(repo=self.repo_path)
        logger.info(f"TTS engine initialized: {self.engine.info}")
        
        # Cache for voice files
        self.voice_cache = {}
        self._load_default_voices()
    
    def _load_default_voices(self):
        """Load default voice references."""
        default_voices = {
            "default": self.engine.voice,
            "female1": self.engine.voice,
        }
        
        # Scan voice directory for additional voices
        if self.voice_dir.exists():
            for voice_file in self.voice_dir.glob("*.wav"):
                voice_name = voice_file.stem
                if voice_name not in default_voices:
                    default_voices[voice_name] = str(voice_file)
        
        self.voice_cache = default_voices
        logger.info(f"Loaded {len(self.voice_cache)} voice references: {list(self.voice_cache.keys())}")
    
    def synthesize(
        self,
        text: str,
        speaker: str = "default",
        speed: float = 1.0,
        volume: float = 1.0,
        tone: str = "neutral",
        intensity: float = 0.0,
        reference_audio_base64: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize speech from text.
        
        Returns:
            WAV audio data as bytes
        """
        reference_bytes = None
        if reference_audio_base64 is not None:
            try:
                reference_bytes = base64.b64decode(reference_audio_base64, validate=True)
                with wave.open(io.BytesIO(reference_bytes), 'rb') as audio:
                    if (audio.getcomptype() != 'NONE' or audio.getnframes() == 0
                            or audio.getnchannels() not in (1, 2)
                            or audio.getnframes() / audio.getframerate() > 30):
                        raise ValueError("参考音频须为不超过 30 秒的非空 PCM WAV")
                    if len(audio.readframes(audio.getnframes())) != audio.getnframes() * audio.getnchannels() * audio.getsampwidth():
                        raise ValueError("参考音频数据不完整")
            except (binascii.Error, wave.Error, EOFError) as exc:
                raise ValueError("参考音频不是有效的 Base64 PCM WAV") from exc
        elif speaker not in self.voice_cache:
            raise ValueError(f"未知音色：{speaker}")

        params = Parameters(speed=speed, volume=volume * 100.0, tone=tone, intensity=intensity)
        # Inference owns mutable model caches. Keep it serialized, while the
        # synchronous endpoint runs in a worker so health requests stay responsive.
        with self.inference_lock, tempfile.TemporaryDirectory(prefix="zhubo-reference-") as folder:
            if reference_bytes is not None:
                voice_path = Path(folder) / "reference.wav"
                voice_path.write_bytes(reference_bytes)
            else:
                voice_path = Path(self.voice_cache[speaker])
            audio_pcm = self.engine.synthesize(text, params, str(voice_path))
        # Engine volume is normally applied by the local playback callback.
        # HTTP clients need the same gain applied to the returned PCM instead.
        audio_pcm = np.clip(audio_pcm.astype(np.float32) * volume, -32768, 32767).astype(np.int16)
        return self._pcm_to_wav(audio_pcm, sample_rate=22050)
    
    @staticmethod
    def _pcm_to_wav(pcm_data: np.ndarray, sample_rate: int = 22050) -> bytes:
        """Convert PCM int16 numpy array to WAV bytes."""
        import wave
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data.tobytes())
        
        return buffer.getvalue()


def create_app(repo_path: Path, voice_dir: Optional[Path] = None) -> FastAPI:
    """Create FastAPI application."""
    
    app = FastAPI(
        title="Zhubo TTS API",
        description="REST API for Zhubo TTS service",
        version="1.0.0"
    )
    
    # Initialize TTS service
    tts_service = TTSService(repo_path=repo_path, voice_dir=voice_dir)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "zhubo-tts",
            "reference_audio_supported": True,
            "engine_info": tts_service.engine.info
        }
    
    @app.post("/tts/synthesize")
    def synthesize(request: SynthesizeRequest):
        """
        Synthesize speech from text.
        
        Returns WAV audio data.
        """
        try:
            wav_data = tts_service.synthesize(
                text=request.text,
                speaker=request.speaker,
                speed=request.speed,
                volume=request.volume,
                tone=request.tone,
                intensity=request.intensity,
                reference_audio_base64=request.reference_audio_base64,
            )
            
            return Response(
                content=wav_data,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=speech.wav"
                }
            )
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Synthesis error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")
    
    @app.get("/voices")
    async def list_voices():
        """List available voice references."""
        return {
            "voices": list(tts_service.voice_cache.keys())
        }
    
    return app


def main():
    parser = argparse.ArgumentParser(description="Zhubo TTS API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--repo", type=Path, default=Path("/home/ln/AI/index-tts"),
                        help="Path to index-tts repository")
    parser.add_argument("--voice-dir", type=Path, default=None,
                        help="Directory containing voice reference files")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of worker processes")
    
    args = parser.parse_args()
    
    app = create_app(repo_path=args.repo, voice_dir=args.voice_dir)
    
    logger.info(f"Starting Zhubo TTS API server on {args.host}:{args.port}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()
