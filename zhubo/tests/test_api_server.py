import base64
import io
import threading
import wave
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from tts_broadcast import api_server


def wav_bytes(samples):
    return api_server.TTSService._pcm_to_wav(np.array(samples, dtype=np.int16))


@pytest.fixture
def service():
    instance = api_server.TTSService.__new__(api_server.TTSService)
    instance.inference_lock = threading.Lock()
    instance.voice_cache = {"default": "default.wav"}
    instance.engine = Mock()
    instance.engine.info = {}
    instance.engine.synthesize.return_value = np.array([20000, -20000], dtype=np.int16)
    return instance


def test_uploaded_reference_reaches_engine_and_is_removed_afterward(service):
    source = wav_bytes([300, -300] * 100)
    seen = []
    def synthesize(text, params, filename):
        seen.append(filename)
        assert Path(filename).read_bytes() == source
        return np.array([1, 2], dtype=np.int16)
    service.engine.synthesize.side_effect = synthesize
    service.synthesize("测试", reference_audio_base64=base64.b64encode(source).decode())
    assert len(seen) == 1
    assert not Path(seen[0]).exists()


@pytest.mark.parametrize("volume,expected", [(0, (0, 0)), (0.5, (10000, -10000)), (2, (32767, -32768))])
def test_http_volume_scales_once_and_clips(service, volume, expected):
    audio = service.synthesize("测试", volume=volume)
    with wave.open(io.BytesIO(audio)) as wav:
        assert tuple(np.frombuffer(wav.readframes(2), dtype=np.int16)) == expected


def test_unknown_speaker_is_not_defaulted(service):
    with pytest.raises(ValueError, match="未知音色"):
        service.synthesize("测试", speaker="missing")
    service.engine.synthesize.assert_not_called()


@pytest.mark.parametrize("payload", ["not base64", base64.b64encode(b"not a wav").decode(), base64.b64encode(wav_bytes([])).decode()])
def test_invalid_reference_is_rejected(service, payload):
    with pytest.raises(ValueError):
        service.synthesize("测试", reference_audio_base64=payload)
    service.engine.synthesize.assert_not_called()


def test_http_contract_uses_reference_audio(monkeypatch, service):
    monkeypatch.setattr(api_server, "TTSService", Mock(return_value=service))
    client = TestClient(api_server.create_app(Path(".")))
    assert client.get("/health").json()["reference_audio_supported"] is True
    response = client.post("/tts/synthesize", json={"text": "测试", "speaker": "unknown"})
    assert response.status_code == 400
