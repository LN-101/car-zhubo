from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app import main


@pytest.fixture
def readiness(monkeypatch):
    reference = Mock(return_value=True)
    gpt = Mock(return_value=True)
    index = Mock()
    index.status.return_value = {"configured": True, "reachable": True}
    adapter = Mock()
    adapter.health_check.return_value = True
    monkeypatch.setattr(main, "_tts_has_reference", reference)
    monkeypatch.setattr(main, "_gpt_sovits_reachable", gpt)
    monkeypatch.setattr(main, "INDEX_TTS2_ENGINE", index)
    monkeypatch.setattr(main, "_get_zhubo_adapter", Mock(return_value=adapter))
    return reference, gpt, index, adapter


def test_healthy_zhubo_does_not_require_other_engines(monkeypatch, readiness):
    reference, gpt, index, adapter = readiness
    monkeypatch.setattr(main.settings, "tts_provider", "zhubo")
    reference.side_effect = AssertionError("Zhubo owns its reference audio")
    gpt.side_effect = AssertionError("GPT-SoVITS must not be probed")
    main._ensure_tts_ready()
    adapter.health_check.assert_called_once_with()
    reference.assert_not_called()
    gpt.assert_not_called()
    index.status.assert_not_called()


@pytest.mark.parametrize("missing", [True, False])
def test_unavailable_zhubo_has_provider_specific_503(monkeypatch, readiness, missing):
    reference, gpt, index, adapter = readiness
    monkeypatch.setattr(main.settings, "tts_provider", "zhubo")
    if missing:
        monkeypatch.setattr(main, "_get_zhubo_adapter", Mock(return_value=None))
    else:
        adapter.health_check.return_value = False
    with pytest.raises(HTTPException) as error:
        main._ensure_tts_ready()
    assert error.value.status_code == 503
    assert "Zhubo TTS" in error.value.detail
    assert "GPT-SoVITS" not in error.value.detail
    reference.assert_not_called()
    gpt.assert_not_called()
    index.status.assert_not_called()


@pytest.mark.parametrize("provider,reference_ok,configured,reachable,expected", [
    ("idextts2", True, True, True, None),
    ("idextts2", False, True, True, "参考音频"),
    ("idextts2", True, False, True, "未配置"),
    ("idextts2", True, True, False, "不可用"),
    ("gpt-sovits", True, True, True, None),
    ("gpt-sovits", False, True, True, "参考音频"),
    ("gpt-sovits", True, True, False, "不可访问"),
])
def test_other_provider_readiness_is_preserved(
    monkeypatch, readiness, provider, reference_ok, configured, reachable, expected
):
    reference, gpt, index, adapter = readiness
    monkeypatch.setattr(main.settings, "tts_provider", provider)
    reference.return_value = reference_ok
    gpt.return_value = reachable
    index.status.return_value = {"configured": configured, "reachable": reachable}
    if expected is None:
        main._ensure_tts_ready()
    else:
        with pytest.raises(HTTPException) as error:
            main._ensure_tts_ready()
        assert error.value.status_code == 503
        assert expected in error.value.detail
    adapter.health_check.assert_not_called()
    if provider == "idextts2":
        gpt.assert_not_called()
    else:
        index.status.assert_not_called()
