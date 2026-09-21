# First streaming playback milestone

## Input and real inference

The CLI accepts direct text or a UTF-8 script file, uses the existing IndexTTS 2.5 repository and checkpoints, and produces 22050 Hz mono PCM with an included reference voice. Model loading and warmup occur once before requests. Default inference uses BF16 and one beam to reduce latency. The sample uses provided automotive resources without disputed price claims. Acceptance: A4.

## Streaming playback

Split text on natural punctuation while preserving decimal numbers and content order. Favor a short first phrase for first-audio latency. Generate successive segments while an audio callback plays queued PCM. Start before all synthesis finishes. Keep bounded lookahead, monotonic segment IDs, and explicit cancellation that clears pending audio. Do not drop text to achieve speed. Save produced speech and report underruns, rather than concealing gaps. Acceptance: A5.

## Measurements and boundaries

Measure real GPU synthesis and local playback. Report model initialization, warmup, input-to-first-PCM, first device output estimated from the audio callback's DAC timestamp, total synthesis time, generated audio duration, RTF, playback duration and underrun count/time. Hardware acoustic output is not measured. Distinguish cold-start and warmed measurements and evaluate the 3-second target on the stated software/device measurement. Provide a runnable command and real report, even when the target is missed. Acceptance: A6.

This milestone does not implement a frontend, live editing, RAG, voice training or pitch/speed/volume controls. Those source requirements remain documented for later milestones.
