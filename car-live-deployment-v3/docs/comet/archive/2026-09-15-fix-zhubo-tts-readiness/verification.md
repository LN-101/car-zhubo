---
generated_from_state_version: 11
---

# Verification

## Current result

- Result: **Archived**
- Verification status: **Checks completed; result confirmed**
- Goal cycle: 2
- Iteration: 1
- Verifier attempt: 1
- Completed: 2026-09-15T10:51:58.723Z
- Summary: All six acceptance criteria passed. Zhubo synthesis and streaming return HTTP 200 with valid audio independent of GPT-SoVITS (A1). Unavailable Zhubo reports honest 503 without probing other engines (A2). IndexTTS2 and GPT-SoVITS readiness logic unchanged (A3). Preset and uploaded voices use their own reference audio; unknown IDs fail explicitly (A4). Clone validation and priming use Zhubo adapter (A5). Service applies clipped volume once; WAV parser streams headers incrementally (A6). Evidence: 149 passed backend/service tests, real synthesis of three presets plus temporary clone, WAV incremental parsing verified, frontend syntax valid.

## Acceptance

| ID | Result | Source | Criterion | Reason |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1: With Zhubo selected and healthy, ordinary synthesis and streaming both return HTTP 200 with non-empty valid audio even when GPT-SoVITS is unavailable. | Zhubo provider returns HTTP 200 with valid audio for both ordinary synthesis and streaming. Implementation: main.py:2288-2295 _ensure_tts_ready() checks only adapter.health_check(), not GPT-SoVITS. Evidence: /tmp/zhubo-tts-verified/results.json shows steady/energetic/friendly presets returned 200 with 223-307KB WAV payload for both /synthesize and /stream endpoints. Test: test_tts_readiness.py test_healthy_zhubo_does_not_require_other_engines confirms GPT-SoVITS is not probed when provider=zhubo. |
| A2 | passed | brief.md | A2: With Zhubo selected but its adapter missing or service unhealthy, readiness returns HTTP 503 naming Zhubo and does not probe GPT-SoVITS. | Unavailable Zhubo returns HTTP 503 with provider-specific message without probing GPT-SoVITS. Implementation: main.py:2290-2295 raises HTTPException(503, 'Zhubo TTS...') when adapter is None or health_check() fails. Test: test_tts_readiness.py test_unavailable_zhubo_has_provider_specific_503 confirms 503 contains 'Zhubo TTS' and not 'GPT-SoVITS', and that gpt_sovits_reachable is never called. |
| A3 | passed | brief.md | A3: Existing IndexTTS2 and GPT-SoVITS readiness behavior remains intact. | IndexTTS2 and GPT-SoVITS readiness branches remain intact. Implementation: main.py:2296-2308 preserves separate provider branches with original reference/configured/reachable checks. Test: test_tts_readiness.py parametrized test_other_provider_readiness_is_preserved validates both idextts2 and gpt-sovits with various reference/configured/reachable states, confirming Zhubo adapter is never called for other providers. |
| A4 | passed | brief.md | A4: Each selected preset or uploaded clone reaches Zhubo with its own reference audio; unknown or missing voices fail explicitly instead of silently selecting a default. | Each voice reaches Zhubo with its own reference audio; unknown voices fail explicitly. Implementation: main.py:1780-1803 _voice_config() resolves preset or uploaded reference, raises HTTPException(404/422) for missing voices. zhubo_adapter.py:26-29 encodes reference bytes as base64 in payload. Test: test_zhubo_voices.py test_selected_voice_is_used_in_both_endpoints verifies steady/energetic/friendly presets and uploaded clone 'voice-test' each use their distinct reference path in both /synthesize and /stream. test_unknown_voice_fails_before_audio_headers confirms 404 for missing voice without calling adapter. |
| A5 | passed | brief.md | A5: Zhubo clone validation and voice priming use Zhubo; unhealthy service status is reported honestly without GPT-SoVITS dependency. | Clone validation and voice priming use Zhubo without GPT-SoVITS dependency. Implementation: main.py:1434-1454 _warm_single_voice() for zhubo provider calls adapter.synthesize with reference audio, probes result, sets synthesis_status. main.py:3027-3039 prime_voice() for zhubo calls _ensure_tts_ready() and _prime_voice_profile(). Test: test_zhubo_voices.py test_clone_probe_and_prime_use_zhubo confirms pending clone calls adapter.synthesize with correct reference, sets status to ready, and prime_voice returns ready=True. Monkeypatch prevents GPT-SoVITS from being reached. |
| A6 | passed | brief.md | A6: Zhubo API volume is applied once with clipping, UI volume remains applied once, and fragmented WAV headers allow PCM to stream before the full payload is buffered. | Zhubo API applies volume once with clipping; UI sends unity gain; WAV headers stream incrementally. Implementation: api_server.py:87 clips audio_pcm to [-32768,32767] after volume scaling. main.py:2224-2271 _wav_data_offset() and _iter_pcm_wav_payload() parse header without waiting for full payload. Test: test_api_server.py test_http_volume_scales_once_and_clips validates (volume=0.5, expected=(10000,-10000)) and (volume=2, expected=(32767,-32768)). test_zhubo_voices.py test_wav_parser_does_not_wait_for_all_pcm confirms _wav_data_offset(audio[:46])==44 and incremental chunk yield. Builder handoff reports 149 backend+service tests passed including service volume tests. |

## Checks

| Check | Command | Working directory | Status | Exit | Duration |
| --- | --- | --- | --- | ---: | ---: |
| Backend and Zhubo service regression tests | PYTHONPATH=/home/ln/AI/zhubo .venv/bin/python -m pytest -q tests /home/ln/AI/zhubo/tests/test_api_server.py | backend | passed | 0 | 5126 ms |
| Frontend JavaScript syntax | --check frontend/app.js | . | passed | 0 | 21 ms |
| Real preset and uploaded clone synthesis | /tmp/verify_zhubo_live.py | . | passed | 0 | 23440 ms |

## Blockers

_None._

## Risks and skipped work

_None reported._

## Previous iterations

| Goal cycle | Iteration | Attempt | Outcome | Unresolved | Summary | Completed |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 0 | recovery | — | Native confirmed acceptance criteria changed | 2026-09-15T10:17:18.105Z |
| 2 | 1 | 1 | pass | — | All six acceptance criteria passed. Zhubo synthesis and streaming return HTTP 200 with valid audio independent of GPT-SoVITS (A1). Unavailable Zhubo reports honest 503 without probing other engines (A2). IndexTTS2 and GPT-SoVITS readiness logic unchanged (A3). Preset and uploaded voices use their own reference audio; unknown IDs fail explicitly (A4). Clone validation and priming use Zhubo adapter (A5). Service applies clipped volume once; WAV parser streams headers incrementally (A6). Evidence: 149 passed backend/service tests, real synthesis of three presets plus temporary clone, WAV incremental parsing verified, frontend syntax valid. | 2026-09-15T10:51:58.723Z |



## Conclusion

All six acceptance criteria passed. Zhubo synthesis and streaming return HTTP 200 with valid audio independent of GPT-SoVITS (A1). Unavailable Zhubo reports honest 503 without probing other engines (A2). IndexTTS2 and GPT-SoVITS readiness logic unchanged (A3). Preset and uploaded voices use their own reference audio; unknown IDs fail explicitly (A4). Clone validation and priming use Zhubo adapter (A5). Service applies clipped volume once; WAV parser streams headers incrementally (A6). Evidence: 149 passed backend/service tests, real synthesis of three presets plus temporary clone, WAV incremental parsing verified, frontend syntax valid.
