# Outcome

Implement the source's mandatory control surface for the streaming broadcast: a local WebUI based on the original IndexTTS webui that supports mid-playback dynamic editing (TTS-03), broadcast parameter controls (TTS-04) and browser-based text/file script input (TTS-01), preserving streaming playback, first-audio latency and smooth-playback behavior (TTS-02, TTS-05, TTS-06).

# Scope

- Build a new broadcast-focused Gradio WebUI in `/home/ln/AI/zhubo`, modeled on the original `/home/ln/AI/index-tts/webui.py` (Chinese labels, control style) and launched with `--host`/`--port`; the index-tts repository stays unmodified.
- WebUI capabilities: script textbox and UTF-8 script file upload to start a broadcast; ordered script item list with live add / edit / delete while playback is unfinished; speed / volume / intonation controls; reference voice selection; live status, metrics and edit-response timing.
- Editing semantics: editing the currently playing item interrupts it immediately and plays the fixed text from its start, then continues normally; editing an already-played item interrupts current playback, plays the corrected item in full, then resumes the interrupted position from the exact interruption point (no repeated audio) and continues in order, only while the broadcast is unfinished; queued edits and inserts update in place and play in order when reached, without interrupting; deleting the playing item interrupts it and continues with the next item; stale queued audio is discarded, never played.
- Parameter controls: speed via IndexTTS 2.5 generation-side `duration_factor`, volume via playback-side gain, intonation via `emo_vector` tone presets. Activation is hybrid: volume immediately, speed and intonation from the next generated segment.
- Keep a bounded playback queue, ordered streaming and honest underrun/latency accounting.
- Keep the existing non-interactive CLI behavior (`run_tts.sh`, `--text`/`--file`, `--runs`, `--voice`, `--output`) working unchanged as a regression.
- Record edit-response timing and applied parameters in the report; update README and tests.

## Source coverage

Source: `whatodo/汽车直播智能体设计与实现.docx` (read completely in milestone 1; the full 52-paragraph coverage map is in `docs/comet/archive/2026-09-10-streaming-tts-broadcast/brief.md`) and its extraction notes `whatodo/直播脚本流式 TTS 动态播报模块.md` (read completely).

| Source unit | Read | Retained semantics | Coverage | Spec / acceptance | Reason |
| --- | --- | --- | --- | --- | --- |
| TTS-01 (DOCX P27-28) | complete | Local script file upload and frontend textbox input | covered | specs/broadcast-webui / A1 | Both input paths delivered by the new WebUI |
| TTS-03 (DOCX P30) | complete | Add, delete and edit the script while audio is unfinished; refresh the streaming audio output after each edit | covered | specs/mid-playback-editing / A2, A3, A6 | Confirmed transition, replay and refresh semantics |
| TTS-04 (DOCX P31) | complete | Customizable speed, volume and intonation | covered | specs/broadcast-parameters / A4 | Confirmed form, activation and ranges |
| TTS-02 (DOCX P29) | complete | Generate and play before the full script is synthesized | covered | specs/streaming-playback / A1, A5 | Preserved under the new architecture |
| TTS-05 (DOCX P31) | complete | Input-to-first-audio latency <= 3 s | covered | specs/streaming-playback / A5 | Regression under the new architecture |
| TTS-06 (DOCX P31) | complete | Smooth playback and a latency report | covered | specs/streaming-playback / A5, A6 | Regression plus edit-response measurement |
| Remaining DOCX units | complete | Extraction record, related modules, optional features and formal deliverables | background/non-goal | - | Not part of this change; see the archived full coverage map |

# Non-goals

No RAG or question-answer speech; no voice cloning or preset-voice management (the original 预设管理 tab stays out of scope); no single-shot synthesis tab; no QwenEmotion text-emotion model (no text emotion descriptions); no formal PDF/PPT reports or demo video in this change; no changes inside the `/home/ln/AI/index-tts` repository.

# Acceptance examples

- A1: The WebUI accepts a script textbox and a UTF-8 script file upload; starting a broadcast plays on the server's local audio device and begins audible playback before the full script finishes synthesizing.
- A2: While a broadcast is unfinished, the UI can add, edit and delete script items; editing the currently playing item interrupts it immediately, plays the fixed text from its start and continues normally; editing an already-played item interrupts current playback, plays the corrected item in full, then resumes the interrupted position from the exact interruption point and continues in order; queued edits and inserts update in place without interrupting; deleting the playing item interrupts it and continues with the next item.
- A3: After any edit, no audio synthesized for the replaced text is heard; stale queued audio for it is discarded rather than played.
- A4: Speed (0.5x-2.0x), volume (0-200 %) and intonation (named presets with intensity 0-1) change the output with hybrid activation: volume applies immediately to playing audio, speed and intonation apply from the next generated segment; applied values are observable in the UI and report.
- A5: Streaming and the existing CLI regress cleanly: playback starts before synthesis completes, warm first device output stays <= 3 s, order is preserved, underruns remain honestly recorded, and non-interactive CLI behavior is unchanged.
- A6: A reproducible report records edit-response timing (control action to refreshed or corrected device output and to resumed playback for interrupt and correction edits; regeneration timing for queued edits) and applied parameter values, alongside the existing latency, RTF and underrun metrics.

# Constraints and invariants

- User preference (project memory): runnable code first, avoid defensive code and overengineering, pursue maximum practical performance; use `/home/ln/AI/index-tts` and integrate in `/home/ln/AI/zhubo`.
- Gradio 5.45.0 is already available in `/home/ln/AI/index-tts/.venv`; do not modify the index-tts repository.
- Keep the existing CLI entry points (`run_tts.sh`, `--text`/`--file`, `--runs`, `--voice`, `--output`) and non-interactive behavior; existing tests keep passing.
- Load the model once per server process (BF16, single beam, existing warmup) and reuse it across broadcasts; the server stays running between broadcasts.
- Preserve 22050 Hz mono PCM16 output, bounded queue, and honest underrun accounting (no hidden gaps, no silent text drops).
- Measurement stays software/device-timestamp based (PortAudio DAC estimate), not acoustic capture.
- Keep the change strictly within the confirmed scope; new user-visible behavior decisions return to Shape.

# Decisions

- WebUI basis: a new broadcast-focused Gradio app in zhubo modeled on the original webui; not a copy of its full synthesis UI and not a modification of the index-tts repository.
- Control surface: the WebUI drives live editing and parameters; the CLI remains for non-interactive playback.
- Editing the currently playing item: immediate interrupt, then play the fixed text from its start and continue normally.
- Editing an already-played item: only while the broadcast is unfinished, interrupt current playback, synthesize and play the corrected item in full, then resume the interrupted position from the exact interruption point (no repeated audio) and continue in order; once the broadcast has finished, the edit only updates the list text.
- Queued edits and inserts: update in place, play in order when reached, no interruption; only editing/deleting the playing item interrupts it.
- Parameter activation: hybrid - volume immediately; speed (`duration_factor`) and intonation (`emo_vector`) from the next generated segment.
- Intonation form: named tone presets (neutral / warm / energetic / steady) with intensity 0-1 mapped to emotion vectors; `use_random=False`.
- Ranges: speed 0.5x-2.0x, volume 0-200 %, intonation intensity 0-1.
- Keep one tightly coupled change; no QwenEmotion model dependency; index-tts repository untouched.
- Workspace: current directory (`/home/ln/AI/zhubo`), branch `feature/new-model-impl` (verified against the current Runtime binding and Git branch).

# Open questions

# Verification expectations

Independent verification covers: unit tests for the broadcast session (edit commands, queue refresh, interrupt-and-replay, correction inserts with exact-position resume, parameter plumbing); a real GPU WebUI run exercising script start, add/edit/delete, each parameter change and edit-response timing; regression of streaming latency, order and underrun accounting; the non-interactive CLI; and inspection of the updated report for edit-response and parameter evidence.
