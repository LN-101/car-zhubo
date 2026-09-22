import base64
from contextlib import contextmanager
import io
import sqlite3
import wave
from unittest.mock import Mock

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.tts.adapters.zhubo_adapter import ZhuboTTSAdapter


def make_wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        wav.writeframes(b"\x10\x00" * 22050)
    return out.getvalue()


@pytest.fixture
def zhubo(monkeypatch, tmp_path):
    monkeypatch.setattr(main.settings, "tts_provider", "zhubo")
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE voices (id TEXT, reference_path TEXT, prompt_text TEXT, prompt_lang TEXT, synthesis_status TEXT, synthesis_message TEXT, provider TEXT)")
    ref = tmp_path / "clone.wav"
    ref.write_bytes(make_wav())
    db.execute("INSERT INTO voices VALUES ('voice-test', ?, '', 'zh', 'ready', '', 'zhubo')", (str(ref),))
    @contextmanager
    def conn():
        yield db
    monkeypatch.setattr(main, "conn", conn)
    monkeypatch.setattr(main, "_audio_quality", lambda path: {"status": "ready" if path and __import__('pathlib').Path(path).is_file() else "missing", "message": "参考音频"})
    adapter = Mock()
    adapter.health_check.return_value = True
    adapter.list_voices.return_value = ["default"]
    adapter.synthesize.return_value = make_wav()
    monkeypatch.setattr(main, "_get_zhubo_adapter", lambda: adapter)
    monkeypatch.setattr(main, "VOICE_WARMED", set())
    monkeypatch.setattr(main, "VOICE_WARMING", set())
    monkeypatch.setattr(main, "_gpt_sovits_reachable", Mock(side_effect=AssertionError("wrong engine")))
    monkeypatch.setattr(main, "_ensure_model_profile_loaded", Mock(side_effect=AssertionError("wrong engine")))
    yield adapter, ref, db
    db.close()


@pytest.mark.parametrize("endpoint", ["synthesize", "stream"])
@pytest.mark.parametrize("voice_id", ["steady", "energetic", "friendly", "voice-test"])
def test_selected_voice_is_used_in_both_endpoints(zhubo, endpoint, voice_id):
    adapter, ref, _ = zhubo
    response = TestClient(main.app).post(f"/api/tts/{endpoint}", json={"text": "验证音色。", "voice_id": voice_id})
    assert response.status_code == 200
    assert response.content[:4] == b"RIFF"
    expected = str(ref) if voice_id == "voice-test" else main.preset_reference_paths(voice_id)[0]
    assert adapter.synthesize.call_args.kwargs["reference_audio"] == expected


@pytest.mark.parametrize("endpoint", ["synthesize", "stream"])
def test_system_default_voice_uses_the_service_default_speaker(zhubo, endpoint):
    """系统默认 has no reference audio and must not need one."""
    adapter, _, db = zhubo
    db.execute("INSERT INTO voices VALUES ('browser-default', '', '', 'zh', 'ready', '', 'browser')")
    response = TestClient(main.app).post(f"/api/tts/{endpoint}", json={"text": "验证音色。", "voice_id": "browser-default"})
    assert response.status_code == 200
    assert response.content[:4] == b"RIFF"
    assert adapter.synthesize.call_args.kwargs["reference_audio"] is None
    assert adapter.synthesize.call_args.kwargs["speaker"] == main.settings.zhubo_default_speaker


@pytest.mark.parametrize("endpoint", ["synthesize", "stream"])
def test_unknown_voice_fails_before_audio_headers(zhubo, endpoint):
    adapter, _, _ = zhubo
    response = TestClient(main.app).post(f"/api/tts/{endpoint}", json={"text": "验证", "voice_id": "missing"})
    assert response.status_code == 404
    adapter.synthesize.assert_not_called()


def test_missing_clone_reference_is_not_substituted(zhubo):
    _, ref, _ = zhubo
    ref.unlink()
    with pytest.raises(HTTPException) as error:
        main._voice_config("voice-test")
    assert error.value.status_code == 422


def test_clone_probe_and_prime_use_zhubo(zhubo, monkeypatch):
    adapter, ref, db = zhubo
    db.execute("UPDATE voices SET synthesis_status='pending'")
    status = Mock()
    monkeypatch.setattr(main, "_set_voice_synthesis_status", status)
    monkeypatch.setattr(main, "_probe_audio_payload", lambda audio: {"status": "ready", "message": "通过", "duration": 1})
    main._warm_single_voice("voice-test")
    assert adapter.synthesize.call_args.kwargs["reference_audio"] == str(ref)
    status.assert_called_once_with("voice-test", "ready", "通过", 1)
    db.execute("UPDATE voices SET synthesis_status='ready'")
    assert main.prime_voice("voice-test")["ready"] is True


def test_latency_benchmark_measures_the_zhubo_engine(zhubo, monkeypatch):
    """效果验证 must not fall through to the GPT-SoVITS branch."""
    adapter, ref, _ = zhubo
    monkeypatch.setattr(main, "_preferred_clone_voice_id", lambda: "voice-test")
    report = TestClient(main.app).post("/api/tests/tts").json()
    assert report["provider"] == "zhubo"
    assert report["voice_id"] == "voice-test"
    assert report["samples"] == 3 and len(report["sample_results"]) == 3
    assert all(result["ok"] for result in report["sample_results"])
    assert report["average_first_audio_ms"] is not None and report["meets_target"] is True
    assert adapter.synthesize.call_count == 3
    assert adapter.synthesize.call_args.kwargs["reference_audio"] == str(ref)


def test_status_does_not_claim_unhealthy_service_is_ready(zhubo):
    adapter, _, _ = zhubo
    adapter.health_check.return_value = False
    status = main.tts_status()
    assert not status["ready"] and not status["reachable"] and not status["streaming"]
    adapter.list_voices.assert_not_called()


def test_wav_parser_does_not_wait_for_all_pcm():
    audio = make_wav()
    assert main._wav_data_offset(audio[:46]) == 44
    chunks = main._iter_pcm_wav_payload(iter([audio[:46], audio[46:]]), include_header=True)
    assert next(chunks) == audio[:44]
    assert next(chunks) == audio[44:46]
    assert b"".join(chunks) == audio[46:]


def test_adapter_transports_audio_content_without_speaker_alias(monkeypatch, tmp_path):
    reference = tmp_path / "voice.wav"
    reference.write_bytes(make_wav())
    def handle(request):
        import json
        payload = json.loads(request.content)
        assert base64.b64decode(payload["reference_audio_base64"]) == reference.read_bytes()
        assert "speaker" not in payload
        return httpx.Response(200, content=make_wav())
    client_class = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handle), **kwargs))
    assert ZhuboTTSAdapter().synthesize("测试", str(reference))[:4] == b"RIFF"


def test_adapter_uses_the_service_default_speaker_without_reference_audio(monkeypatch):
    def handle(request):
        import json
        payload = json.loads(request.content)
        assert "reference_audio_base64" not in payload
        assert payload["speaker"] == "default"
        return httpx.Response(200, content=make_wav())
    client_class = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handle), **kwargs))
    assert ZhuboTTSAdapter().synthesize("测试")[:4] == b"RIFF"
