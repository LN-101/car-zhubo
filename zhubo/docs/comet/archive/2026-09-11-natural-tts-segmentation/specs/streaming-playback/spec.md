# Streaming broadcast playback

## Input and real inference

The CLI accepts direct text or a UTF-8 script file, uses the existing IndexTTS 2.5 repository and checkpoints, and produces 22050 Hz mono PCM with an included reference voice. Model loading and warmup occur once before requests. Default inference uses BF16 and one beam to reduce latency. The sample uses provided automotive resources without disputed price claims. Existing `run_tts.sh`, `--text`/`--file`, `--runs`, `--voice` and `--output` behavior remains available.

## Script segmentation

CLI and Web broadcast share natural-punctuation script segmentation, including Web initial task creation, edits and insertions. Existing Chinese/English sentence punctuation, commas, semicolons and newlines define candidate phrase boundaries; decimal dots remain within numbers. Preserve spoken content, punctuation and order, with existing boundary-whitespace trimming and empty-input behavior.

The first two segments use a 16-character grouping target and later segments use a 32-character grouping target. These targets guide combining adjacent short phrases only. They never authorize slicing within a phrase. A phrase longer than a target is kept intact through its natural boundary or end of input. In particular, 我们继续看看它的空间和日常使用体验。 must be submitted as a complete phrase, including when an already segmented phrase is processed again during Web job creation. No application task may contain only 验。 as a consequence of the old character limit. Acceptance: A1, A2, A3, A4 in brief.md.

Unusually long phrases without punctuation remain intact at the application layer. IndexTTS retains its existing 120-token per-segment handling; this capability does not promise absence of model-side segmentation or arbitrary-length prosody guarantees. Favor short natural phrases for first-audio latency, without breaking words to meet a character target.

## Streaming playback

Generate successive segments while an audio callback plays queued PCM. Start before all synthesis finishes. Keep bounded lookahead, monotonic segment IDs, and explicit cancellation that clears pending audio. Do not drop text to achieve speed. Save produced speech and report underruns, rather than concealing gaps.

## Measurements and boundaries

Measure real GPU synthesis and local playback. Report model initialization, warmup, input-to-first-PCM, first device output estimated from the audio callback's DAC timestamp, total synthesis time, generated audio duration, RTF, playback duration and underrun count/time. Hardware acoustic output is not measured. Distinguish cold-start and warmed measurements and evaluate the 3-second target on the stated software/device measurement. Provide a runnable command and real report, even when the target is missed.

The broadcast WebUI adds live script editing and speed, volume and intonation controls as specified by the broadcast-webui, mid-playback-editing and broadcast-parameters capabilities. Preserve streaming order and bounded lookahead during edits, discard stale audio, and record edit-response timing and applied parameters alongside latency metrics. Warm first device output must remain <= 3 seconds. Keeping longer phrases intact can affect latency; actual measurements must disclose misses or unavailable timing checks. RAG and voice training remain outside this capability.
