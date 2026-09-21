# Outcome

Restore Zhubo TTS synthesis, selected voice identity, clone validation, and streaming without a GPT-SoVITS dependency.

# Scope

Repair the Zhubo flow in the backend, its adapter, the Zhubo API service, and directly related frontend playback behavior. Inspect related TTS bugs with a separate read-only Pi process. Verify preset and uploaded reference audio, ordinary and streaming synthesis, clone validation/priming, readiness, volume, and WAV streaming.

# Non-goals

No engine replacement, unrelated UI redesign, unrelated cleanup, or changes to GPT-SoVITS model internals.

# Acceptance examples

- A1: With Zhubo selected and healthy, ordinary synthesis and streaming both return HTTP 200 with non-empty valid audio even when GPT-SoVITS is unavailable.
- A2: With Zhubo selected but its adapter missing or service unhealthy, readiness returns HTTP 503 naming Zhubo and does not probe GPT-SoVITS.
- A3: Existing IndexTTS2 and GPT-SoVITS readiness behavior remains intact.

- A4: Each selected preset or uploaded clone reaches Zhubo with its own reference audio; unknown or missing voices fail explicitly instead of silently selecting a default.
- A5: Zhubo clone validation and voice priming use Zhubo; unhealthy service status is reported honestly without GPT-SoVITS dependency.
- A6: Zhubo API volume is applied once with clipping, UI volume remains applied once, and fragmented WAV headers allow PCM to stream before the full payload is buffered.

# Constraints and invariants

Reuse the existing Zhubo adapter health check. Preserve unrelated existing files. Do not add model or credential files to Git.

# Decisions

The user authorized repair in /home/ln/AI/car-live-deployment-v3 current directory and modification or deletion of useless Claude changes. The user authorized creating this directory as a Git repository. The explained repair scope is the common Zhubo readiness check and real ordinary/streaming audio validation.

The user explicitly requested fixing the voice routing bug plus other related TTS bugs and authorized a new independent Pi process for review. Reference audio travels with requests; existing local files remain the source.

# Open questions

None.

# Verification expectations

Regression checks for all provider branches, actual HTTP synthesis and stream requests, and inspection of returned WAV/PCM data. Independent review requires an available separate reviewer execution.
