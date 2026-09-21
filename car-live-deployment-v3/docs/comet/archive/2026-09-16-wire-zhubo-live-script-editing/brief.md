# Outcome

Make the car-live-deployment-v3 live console support the item-level dynamic script editing model that already exists in the zhubo `tts_broadcast` broadcast session, driven by an authoritative backend live-session item model while the browser keeps playing the streamed PCM.

# Scope

Port the zhubo live-edit semantics (ordered script items with stable ids, per-item text/revision/played state, edit/add/delete during playback, played-item protection, stale-audio discard) into the car-live-deployment-v3 live path:

- Backend live session holds an ordered item list (id, text, revision, status) for the broadcast.
- Backend exposes item operations (list, edit, add at position, delete) and playback progress for the current session.
- Live console shows a 实时话术 item table (编号/状态/话术) with edit, add-after-position and delete, plus already-played protection.
- The browser playback engine consumes the item list, tags each synthesized request with its item id/revision, and discards audio whose revision is no longer current.
- Restore phrase-level streaming on the live zhubo path so first audio no longer waits for a whole multi-sentence batch to finish synthesizing.
- The zhubo TTS synthesis path (`/api/tts/synthesize`, `/api/tts/stream`, the selected-provider readiness behavior) and the browser Web Audio playback remain the audio transport.

Reference implementation for the edit semantics: `/home/ln/AI/zhubo/tts_broadcast/session.py` and `/home/ln/AI/zhubo/docs/comet/specs/mid-playback-editing/spec.md` (read as implementation reference, not a requirements source).

# Non-goals

- No change to the zhubo repository itself.
- No server-side sounddevice playback; the audio device stays the browser's default output.
- No change to models, providers, voice cloning/calibration, RAG or question answering.
- No unrelated UI redesign, unrelated cleanup, or Live2D behavior change beyond what the new playback loop requires.
- The first-audio optimization is scoped to the live zhubo path; other providers keep their existing batching and cross-sentence prosody strategy.
- Item-level edit/add/delete during playback is scoped to engines that stream one item per request (zhubo). Batched engines (GPT-SoVITS, IndexTTS2) keep their batching and use the whole-script “重新同步脚本” path instead, with the item controls disabled and a hint shown.

# Acceptance examples

- A1: 直播台新增“实时话术”条目表，逐条显示编号/状态/话术；可选中条目编辑文本、在指定编号之后新增条目、删除条目；条目来自后端会话而不是仅存在于浏览器内存。
- A2: 修改正在播报的条目会立即中断该条，并从修订文本的开头重新播报，然后按顺序继续后续条目。
- A3: 修改尚未播报的条目就地替换文本，不打断当前播报，轮到该条时播出新文本。
- A4: 新增条目插入到指定位置并按顺序播出，不打断当前正在播报的内容。
- A5: 删除尚未播报的条目会将其移除；删除正在播报的条目会中断它并继续下一条。
- A6: 任何改稿之后，为被替换文本已经合成但尚未播出的音频都不会被播出。
- A7: 已经播完的条目禁止修改或删除，界面给出提示，后端也拒绝该操作。
- A8: 浏览器播放引擎按条目 id/revision 请求与丢弃音频，过期 revision 的音频不进入播放队列。
- A9: 暖机后点击“开始播报”，浏览器首个有声帧在 2.0 秒内；zhubo 直播请求按短语分段流式返回，首个音频不等待整批文本合成完成。
- A10: IndexTTS2 与 GPT-SoVITS 的既有分批与跨句韵律行为不回归。

# Constraints and invariants

- Preserve the selected-provider readiness checks, voice gating, synthesis parameters and existing audio transport (`/api/tts/synthesize`, `/api/tts/stream`).
- Preserve pause/resume/stop, continuous cancellation, Live2D lip sync, preview and statistics paths.
- Keep the existing sessions table behavior for script/version/state; the item model is the authoritative live editing state.
- Only implementation and artifacts of this change are committed; unrelated user changes are preserved.

# Decisions

- The user selected option A for all three questions: (Q1) backend live-session item model with browser playback; (Q2) played items are protected from edit/delete, matching zhubo's current behavior; (Q3) add a 实时话术 item table with edit/add/delete.
- The zhubo `tts_broadcast` session/edit model is the reference for the editing semantics; the car-live browser playback architecture is kept.
- The zhubo repository is not modified.
- Q1 = option A: editing the currently playing item interrupts that item immediately, replays it from the start of the revised text, then continues with the following items in order (matches zhubo). This replaces the current car-live “finish the current phrase and switch at the next natural pause” behavior, and `docs/DEMO_RUNBOOK.md` must be updated accordingly.
- Q2 = option A: keep the script textbox as the initial script input, add a 实时话术 item table, and keep the whole-script button as “重新同步脚本” that diffs the textbox against the backend item list (add/edit/delete unplayed items) and rejects the operation when it would touch an already-played item.
- First-audio regression cause (verified in code): the live path merges five sentences into one synthesis request (`frontend/app.js` `STREAM_BATCH_UNITS=5` with `stream_batch=true`, and `_tts_stream_units` collapsing `unitized && stream_batch` to a single unit), while the zhubo HTTP wrapper `tts_broadcast/api_server.py` synthesizes the whole text and returns one complete WAV. Live requests now go item by item through the existing natural-punctuation splitter, so the first audio no longer waits for the whole batch. No special first-sentence/phrase handling is added.
- The user chose to fold the first-audio work into this change (Q1 = A), to restore phrase-level streaming on the live zhubo path (Q2 = B), and set the target at first audio under 2.0 s (Q3 = A, relaxed from 1.5 s). The zhubo repository is still not modified.

# Open questions

None.

# Verification expectations

Regression checks for the existing provider/stream/readiness behavior, browser live playback (start/pause/resume/stop/cancel), Live2D lip sync, and the statistics event path; plus end-to-end item-level edit/add/delete checks against a real or simulated TTS provider, including stale-audio discard and played-item protection. Measure the live first-audio time on a warmed engine and record the actual value, and confirm the other providers' batching behavior is unchanged. The verification report records which checks actually ran.
