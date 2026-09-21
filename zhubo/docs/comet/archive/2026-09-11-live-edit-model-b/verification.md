---
generated_from_state_version: 8
---

# Verification

## Current result

- Result: **Archived**
- Verification status: **Checks completed; result confirmed**
- Goal cycle: 1
- Iteration: 1
- Verifier attempt: 1
- Completed: 2026-09-11T11:27:02.675Z
- Summary: Independent read-only verification passes A1–A6 based on inspected implementation, test assertions, Runtime-owned results and raw measurement artifacts. Read brief.md and all five complete specs first and the details-page Builder handoff last; Builder and prior-review assertions were not used as standalone proof. Preserved projectRoot and verificationRoot=/home/ln/AI/zhubo, changeDir=/home/ln/AI/zhubo/docs/comet/changes/live-edit-model-b, briefRef=brief.md, supervisorStateRef=null and changeDir-relative spec refs. No files modified or commands executed.

## Acceptance

| ID | Result | Source | Criterion | Reason |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1: The WebUI accepts a script textbox and a UTF-8 script file upload; starting a broadcast plays on the server's local audio device and begins audible playback before the full script finishes synthesizing. | Inspected the Chinese Gradio controls, UTF-8 upload handling, empty-input rejection, reference-voice plumbing, reusable Engine and local PortAudio output. Runtime's real Gradio/GPU check passed. outputs/comet-verify-live records text first device output at 0.973 s versus synthesis completion at 43.400 s; uploaded-file output began at 1.015 s with only the first item generated before deliberate stop. |
| A2 | passed | brief.md | A2: While a broadcast is unfinished, the UI can add, edit and delete script items; editing the currently playing item interrupts it immediately, plays the fixed text from its start and continues normally; editing an already-played item interrupts current playback, plays the corrected item in full, then resumes the interrupted position from the exact interruption point and continues in order; queued edits and inserts update in place without interrupting; deleting the playing item interrupts it and continues with the next item. | Session scheduling and Runtime-passed deterministic tests cover current-item restart, queued edits/inserts without interruption, current/queued/played deletion, boundary correction, nested corrections and editing after completion. Real GPU evidence records correction interrupting item 2 at frame 7168 and resuming the same segment at frame 7168 after corrected item 1; the added item plays and the deleted queued item does not. |
| A3 | passed | brief.md | A3: After any edit, no audio synthesized for the replaced text is heard; stale queued audio for it is discarded rather than played. | Edits replace jobs under the callback's shared lock, invalidate in-flight results by job identity/revision and remove stale queued PCM. Deterministic PCM tests verify current restart, queued replacement, suspended-item replacement and stale in-flight generation rejection. Runtime GPU evidence marks displaced generation 1 discarded and contains no playback event for it. |
| A4 | passed | brief.md | A4: Speed (0.5x-2.0x), volume (0-200 %) and intonation (named presets with intensity 0-1) change the output with hybrid activation: volume applies immediately to playing audio, speed and intonation apply from the next generated segment; applied values are observable in the UI and report. | Parameters enforce the specified ranges, map speed to duration_factor=1/speed and scale the named eight-dimensional tone vectors. Engine passes these values to IndexTTS with use_random=False and QwenEmotion disabled. Callback gain uses current volume with PCM16 clipping; generation captures parameters when synthesis begins. Runtime-passed tests verify gain, clipping and preservation of queued parameters. Real GPU records include neutral, warm, energetic and steady generations, with applied values exposed through UI snapshots and reports. |
| A5 | passed | brief.md | A5: Streaming and the existing CLI regress cleanly: playback starts before synthesis completes, warm first device output stays <= 3 s, order is preserved, underruns remain honestly recorded, and non-interactive CLI behavior is unchanged. | Runtime reports all 25 unit tests and both launch-help checks passed. Inspected CLI entry points retain --text/--file, --runs, --voice and --output. docs/live-edit-evidence/cli.json records two real CLI runs with ordered IDs 0,1,2, streaming before synthesis completion, first device output 0.956/1.035 s and zero underruns. Runtime WebUI evidence also meets the warm 3 s target and honestly records two queue underruns totaling 2.926 s. Tests cover bounded resident PCM, ordering, decimal-preserving segmentation and cancellation. |
| A6 | passed | brief.md | A6: A reproducible report records edit-response timing (control action to refreshed or corrected device output and to resumed playback for interrupt and correction edits; regeneration timing for queued edits) and applied parameter values, alongside the existing latency, RTF and underrun metrics. | README and docs/实时改稿测试报告.md provide reproduction commands, measurement definitions and linked raw evidence. Session records edit action timestamps, regeneration, refreshed output, continuation timing, interruption frames, applied generation parameters, latency, RTF and underruns, and saves metrics plus callback-output WAV. Runtime evidence includes current-edit output/continuation at 1.751/6.372 s, correction output/resume at 1.610/4.222 s, queued regeneration at 37.645 s and deletion continuation at 0.209 s. Published report values agree with its separate docs/live-edit-evidence run. |

## Checks

| Check | Command | Working directory | Status | Exit | Duration |
| --- | --- | --- | --- | ---: | ---: |
| 25 playback and live editing tests | LD_LIBRARY_PATH=/home/ln/AI/zhubo/.local/usr/lib/x86_64-linux-gnu /home/ln/AI/index-tts/.venv/bin/python -m unittest discover -s tests -v | . | passed | 0 | 272 ms |
| Existing CLI argument compatibility | run_tts.sh --help | . | passed | 0 | 190 ms |
| WebUI launch arguments | run_webui.sh --help | . | passed | 0 | 1410 ms |
| Real Gradio GPU playback and live controls | tools/validate_live_webui.py --url http://127.0.0.1:7861 --output outputs/comet-verify-live | . | passed | 0 | 52235 ms |

## Blockers

_None._

## Risks and skipped work

- Timing and exact resume are verified at the software PCM/PortAudio DAC boundary, not by acoustic capture. Already-submitted device buffers cannot be withdrawn; controls affect subsequent callbacks.
- Real integration exercises Gradio event endpoints. Browser rendering, physical listening, subjective tone quality and replacement reference-voice upload were not independently exercised.
- The file-upload integration run deliberately stops after first output; it establishes upload/start/stop behavior, not a completed file broadcast.
- CLI regression evidence includes recorded GPU runs plus current Runtime unit/help checks; Runtime did not rerun real CLI inference in this dispatch.
- Resident pending PCM is bounded, but full-session recording grows in memory and retained snapshots consume temporary disk space. No long-duration stress evidence was supplied.
- Stopping clears playback, but an in-flight GPU inference finishes before another broadcast can start.
- No repository-diff check was available in the supplied Runtime results to independently establish that the upstream index-tts repository remained unchanged.

## Previous iterations

| Goal cycle | Iteration | Attempt | Outcome | Unresolved | Summary | Completed |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | pass | — | Independent read-only verification passes A1–A6 based on inspected implementation, test assertions, Runtime-owned results and raw measurement artifacts. Read brief.md and all five complete specs first and the details-page Builder handoff last; Builder and prior-review assertions were not used as standalone proof. Preserved projectRoot and verificationRoot=/home/ln/AI/zhubo, changeDir=/home/ln/AI/zhubo/docs/comet/changes/live-edit-model-b, briefRef=brief.md, supervisorStateRef=null and changeDir-relative spec refs. No files modified or commands executed. | 2026-09-11T11:27:02.675Z |



## Conclusion

Independent read-only verification passes A1–A6 based on inspected implementation, test assertions, Runtime-owned results and raw measurement artifacts. Read brief.md and all five complete specs first and the details-page Builder handoff last; Builder and prior-review assertions were not used as standalone proof. Preserved projectRoot and verificationRoot=/home/ln/AI/zhubo, changeDir=/home/ln/AI/zhubo/docs/comet/changes/live-edit-model-b, briefRef=brief.md, supervisorStateRef=null and changeDir-relative spec refs. No files modified or commands executed.
