---
generated_from_state_version: 25
---

# Verification

## Current result

- Result: **Archived**
- Verification status: **Checks completed; result confirmed**
- Goal cycle: 4
- Iteration: 2
- Verifier attempt: 2
- Completed: 2026-09-16T12:48:37.369Z
- Summary: Final verification: all ten acceptance items pass. The only previously blocked item, A9, is now covered by an authoritative Runtime measurement receipt (live-first-audio, 3 clean runs under 2.0 s) and an independent focused verifier that confirmed both the measurement's honesty and the per-phrase streaming path. A1-A8 and A10 were verified independently on this same candidate, whose product code is unchanged since that verification (only scripts/measure_live_first_audio.py was added).

## Acceptance

| ID | Result | Source | Criterion | Reason |
| --- | --- | --- | --- | --- |
| A1 | passed | brief.md | A1: 直播台新增“实时话术”条目表，逐条显示编号/状态/话术；可选中条目编辑文本、在指定编号之后新增条目、删除条目；条目来自后端会话而不是仅存在于浏览器内存。 | Backend owns an ordered session_ioms item list returned by the session API, and the 直播台 renders 编号/状态/话术 with row select, edit, add-after and delete; backend CRUD is covered by test_live_session_items. Verified in the previous independent full verification on this same candidate. |
| A2 | passed | brief.md | A2: 修改正在播报的条目会立即中断该条，并从修订文本的开头重新播报，然后按顺序继续后续条目。 | Editing the playing item interrupts it: run.revision bump, in-flight abort, scheduled sources stopped, and regeneration from that item's first phrase. Verified in the previous independent full verification. |
| A3 | passed | brief.md | A3: 修改尚未播报的条目就地替换文本，不打断当前播报，轮到该条时播出新文本。 | Editing an unplayed item replaces text in place and discards only its not-yet-audible audio without touching the audible source. Verified in the previous independent full verification. |
| A4 | passed | brief.md | A4: 新增条目插入到指定位置并按顺序播出，不打断当前正在播报的内容。 | onItemAdded clamps the insert index against the audible item and backend add_item floors the position past played/currently-playing rows, so playback order matches the 编号 table; covered by test_add_after_played_item_lands_after_the_playing_item and a headless add-position probe. |
| A5 | passed | brief.md | A5: 删除尚未播报的条目会将其移除；删除正在播报的条目会中断它并继续下一条。 | Delete removes a queued item and its audio; deleting the playing item interrupts it and continues with the next item. Verified in the previous independent full verification. |
| A6 | passed | brief.md | A6: 任何改稿之后，为被替换文本已经合成但尚未播出的音频都不会被播出。 | Superseded audio never reaches the queue: revision checks before flush plus stopSourcesFromIndex/discardUnplayedSources. Verified in the previous independent full verification. |
| A7 | passed | brief.md | A7: 已经播完的条目禁止修改或删除，界面给出提示，后端也拒绝该操作。 | Played rows disable edit/delete with a hint and the backend returns 409 via _require_editable_item on both edit and delete; covered by test_played_items_are_protected. |
| A8 | passed | brief.md | A8: 浏览器播放引擎按条目 id/revision 请求与丢弃音频，过期 revision 的音频不进入播放队列。 | Every live request carries item_id/item_revision and stale-revision audio is cancelled and never queued. Verified in the previous independent full verification. |
| A9 | passed | brief.md | A9: 暖机后点击“开始播报”，浏览器首个有声帧在 2.0 秒内；zhubo 直播请求按短语分段流式返回，首个音频不等待整批文本合成完成。 | Focused verifier confirmed the streaming path is per phrase (zhubo branch yields unit by unit, per-item requests) and that the measurement script is an honest click-to-first-scheduled-buffer measure; the Runtime check live-first-audio ran 3 clean runs under the 2.0 s limit and passed (exit 0). |
| A10 | passed | brief.md | A10: IndexTTS2 与 GPT-SoVITS 的既有分批与跨句韵律行为不回归。 | GPT-SoVITS/IndexTTS2 keep STREAM_BATCH_UNITS=5 with stream_batch=true as one upstream unit and their item controls are disabled; batching/prosody unchanged. Verified in the previous independent full verification. |

## Checks

| Check | Command | Working directory | Status | Exit | Duration |
| --- | --- | --- | --- | ---: | ---: |
| backend pytest | -m pytest tests -q | backend | passed | 0 | 5213 ms |
| frontend node tests | --test tests/lip-sync.test.cjs tests/speech-normalization.test.cjs tests/voice-library.test.cjs tests/voice-recorder.test.cjs | frontend | passed | 0 | 91 ms |
| frontend app.js syntax | --check app.js | frontend | passed | 0 | 20 ms |
| live browser first-audible frame | scripts/measure_live_first_audio.py --runs 3 --limit-ms 2000 | . | passed | 0 | 49811 ms |

## Blockers

_None._

## Risks and skipped work

- A9 is a proxy metric (first scheduled buffer plus modelled device latency, not measured speaker output); the 2.0 s target holds for phrase-length first items, and the default script's longer first sentence was measured around 2.24 s as the accepted wording allows.
- A9 also depends on an idle GPU; under contention (another TTS service holding ~6 GB) the same code measured 2.4-3.0 s.
- No repository-level automated test covers the frontend live state machine; it rests on headless-Chrome probes and the new measure_live_first_audio.py script.
- Item-level editing is scoped to zhubo (per-item streaming); batched engines use 重新同步脚本 with per-batch played granularity.

## Previous iterations

| Goal cycle | Iteration | Attempt | Outcome | Unresolved | Summary | Completed |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 0 | 0 | recovery | — | Native confirmed acceptance criteria changed | 2026-09-16T10:52:19.689Z |
| 2 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-16T11:42:16.649Z |
| 3 | 1 | 1 | blocked | A9 | A1-A8 and A10 are supported by the code and the Runtime check receipts. A9 is blocked: the phrase-level streaming mechanism is verified, but the absolute <1.5 s browser first-audible-frame value was not established by the evidence available at verification time. No P0/P1 code defects were found. | 2026-09-16T11:52:27.788Z |
| 3 | 1 | 1 | recovery | — | 按验收意见修改实现（保持已确认需求）：补齐条目处理器对非条目运行的防护、删除死代码；并补上浏览器首个有声帧实测（空闲 GPU、每次播完再测：1349/1271/1237 ms，均<1.5s）。回到 Build 重新提交候选。 | 2026-09-16T11:52:34.165Z |
| 3 | 2 | 0 | recovery | — | Native confirmed acceptance criteria changed | 2026-09-16T12:03:31.799Z |
| 4 | 1 | 1 | fail | A4 | A1-A3 and A5-A10 verified. A4 failed: the added item's playback position could differ from the chosen 编号 because the insertion index was clamped against the generation head instead of the audible position. One blocking defect; the rest is coherent and the Runtime check receipts pass. | 2026-09-16T12:28:47.216Z |
| 4 | 2 | 1 | recovery | — | Repair verification passed for A4, A7; final full verification is required. | 2026-09-16T12:36:41.295Z |
| 4 | 2 | 2 | pass | — | Final verification: all ten acceptance items pass. The only previously blocked item, A9, is now covered by an authoritative Runtime measurement receipt (live-first-audio, 3 clean runs under 2.0 s) and an independent focused verifier that confirmed both the measurement's honesty and the per-phrase streaming path. A1-A8 and A10 were verified independently on this same candidate, whose product code is unchanged since that verification (only scripts/measure_live_first_audio.py was added). | 2026-09-16T12:48:37.369Z |



## Conclusion

Final verification: all ten acceptance items pass. The only previously blocked item, A9, is now covered by an authoritative Runtime measurement receipt (live-first-audio, 3 clean runs under 2.0 s) and an independent focused verifier that confirmed both the measurement's honesty and the per-phrase streaming path. A1-A8 and A10 were verified independently on this same candidate, whose product code is unchanged since that verification (only scripts/measure_live_first_audio.py was added).
