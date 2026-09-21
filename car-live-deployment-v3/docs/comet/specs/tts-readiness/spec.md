# Selected TTS provider readiness

Both /api/tts/synthesize and /api/tts/stream must validate the selected provider before generating audio.

For Zhubo, resolve the existing adapter, return HTTP 503 with a Zhubo-specific message if it is unavailable or its health check fails, and allow synthesis otherwise. Zhubo readiness does not depend on GPT-SoVITS reachability or reference audio.

For IndexTTS2, retain reference-audio, configuration and reachability checks and existing failures. For GPT-SoVITS, retain reference-audio and reachability checks and existing failures.

A healthy Zhubo service must produce non-empty valid audio through both ordinary and streaming endpoints even with GPT-SoVITS unavailable. Preserve existing voice gating, synthesis parameters and audio transport behavior.

Selected voice identity must be preserved through ordinary synthesis, streaming, clone validation and voice priming. Resolve preset and uploaded reference audio in the backend and send its content to Zhubo. Unknown IDs or absent references fail explicitly. Uploaded pending clones become ready only after actual synthesis with their own reference passes the existing audio probe. No Zhubo path invokes GPT-SoVITS priming or calibration.

Health status reflects the real Zhubo health check. Zhubo API volume scales PCM with saturation; frontend playback applies its volume once. The shared WAV parser identifies complete headers without waiting for the entire advertised data chunk, preserving first-audio streaming.
