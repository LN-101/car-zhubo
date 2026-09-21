"""HTTP adapter for the Zhubo TTS service."""
import base64
from pathlib import Path

import httpx


class ZhuboTTSAdapter:
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url.rstrip("/")

    def synthesize(
        self,
        text: str,
        reference_audio: str,
        speed: float = 1.0,
        volume: float = 1.0,
        tone: str = "neutral",
        intensity: float = 0.0,
    ) -> bytes:
        # Send audio content so voice identity does not depend on service-local
        # speaker aliases or on a shared filesystem between the two servers.
        payload = {
            "text": text,
            "reference_audio_base64": base64.b64encode(Path(reference_audio).read_bytes()).decode("ascii"),
            "speed": speed,
            "volume": volume,
            "tone": tone,
            "intensity": intensity,
        }
        with httpx.Client(timeout=120.0, trust_env=False) as client:
            response = client.post(f"{self.base_url}/tts/synthesize", json=payload)
            response.raise_for_status()
            return response.content

    def list_voices(self) -> list:
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            response = client.get(f"{self.base_url}/voices")
            response.raise_for_status()
            return response.json()["voices"]

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5.0, trust_env=False) as client:
                response = client.get(f"{self.base_url}/health")
                status = response.json() if response.status_code == 200 else {}
                return status.get("status") == "healthy" and status.get("reference_audio_supported") is True
        except (httpx.HTTPError, ValueError, AttributeError):
            return False
