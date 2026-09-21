"""
TTS Broadcast Adapter
Bridge between car-live-deployment-v3 and zhubo/tts_broadcast
"""
import io
import sys
from pathlib import Path
from typing import Optional
import wave
import numpy as np

# Add zhubo to Python path
ZHUBO_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "zhubo"
if ZHUBO_ROOT.exists():
    sys.path.insert(0, str(ZHUBO_ROOT))

try:
    from tts_broadcast.engine import Engine, Parameters
    TTS_BROADCAST_AVAILABLE = True
except ImportError:
    TTS_BROADCAST_AVAILABLE = False
    Engine = None
    Parameters = None


class TTSBroadcastAdapter:
    """Adapter to use zhubo/tts_broadcast in car-live-deployment-v3"""
    
    def __init__(
        self,
        model_path: str,
        reference_audio: str,
        upload_dir: str,
        device: str = "cuda",
        threads: int = 4
    ):
        if not TTS_BROADCAST_AVAILABLE:
            raise RuntimeError(
                "tts_broadcast module not available. "
                "Please ensure zhubo/tts_broadcast is properly set up."
            )
        
        self.model_path = Path(model_path)
        self.reference_audio = Path(reference_audio)
        self.upload_dir = Path(upload_dir)
        self.device = device
        
        # Initialize TTS engine
        # Engine expects the index-tts repo path, not the model path
        index_tts_repo = self.model_path.parent.parent if self.model_path.name == "config.yaml" else self.model_path.parent
        
        self.engine = Engine(repo=index_tts_repo, threads=threads)
        self.sample_rate = 22050
    
    def generate(
        self,
        text: str,
        speed: float = 1.0,
        volume: float = 1.0,
        tone: str = "neutral",
        intensity: float = 0.3,
        reference_audio: Optional[str] = None
    ) -> bytes:
        """
        Generate TTS audio with enhanced parameters.
        
        Args:
            text: Text to synthesize
            speed: Speech speed (0.6-1.6)
            volume: Volume level (0.0-2.0)
            tone: Tone preset (neutral, warm, energetic, steady)
            intensity: Emotion intensity (0.0-1.0)
            reference_audio: Override default reference audio
            
        Returns:
            WAV audio bytes
        """
        # Create Parameters object
        # volume in Parameters is 0-200, convert from 0.0-2.0
        params = Parameters(
            speed=speed,
            volume=volume * 100,
            tone=tone,
            intensity=intensity
        )
        
        # Use provided reference audio or default
        voice = reference_audio if reference_audio else str(self.reference_audio)
        
        # Generate audio (returns numpy int16 PCM)
        pcm = self.engine.synthesize(text, params, voice)
        
        # Convert PCM to WAV bytes
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm.tobytes())
        
        return wav_buffer.getvalue()
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.engine, 'cleanup'):
            self.engine.cleanup()
