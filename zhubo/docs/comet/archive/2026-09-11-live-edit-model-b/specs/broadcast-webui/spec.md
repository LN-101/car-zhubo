# Broadcast WebUI

## Application and launch

A local Gradio WebUI integrated in `/home/ln/AI/zhubo` and modeled on the original IndexTTS webui (Chinese labels and control style), launched through `run_webui.sh` with `--host` and `--port` options. The `/home/ln/AI/index-tts` repository stays unmodified. The model loads once when the server starts (BF16, one beam, existing warmup) and is reused by every broadcast; the server stays running between broadcasts. Acceptance: A1.

## Script input and broadcast control

The UI provides a script textbox and a UTF-8 script file upload; either can start a broadcast, which plays through the server machine's local audio device. An empty script is rejected with a visible message and starts no broadcast. A stop control cancels playback and pending synthesis. The reference voice defaults to the bundled IndexTTS example voice and can be replaced by a local wav file; a voice change applies to the next broadcast start. Acceptance: A1.

## Live session view

While a broadcast runs, the UI shows the ordered script items with the currently playing item marked, controls to add, edit and delete items, the speed / volume / intonation controls, and live status metrics such as first-audio latency, now-playing item, underruns and edit-response timing. Editing behavior is specified by the mid-playback editing capability, and parameter behavior by the broadcast parameters capability. Acceptance: A1, A2, A4, A6.

## Boundaries

No preset management, no single-shot synthesis tab, no RAG, no voice cloning and no text-emotion model handling. The non-interactive command line keeps working independently of the WebUI. Acceptance: A5.
