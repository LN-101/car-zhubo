# Live script editing for the car-live console

The car-live live console broadcasts an ordered script while the browser plays the streamed TTS PCM. This capability gives that broadcast an authoritative ordered item model with the same editing semantics as the zhubo `tts_broadcast` broadcast session, while keeping the selected-provider synthesis and browser playback unchanged.

## Session item model

A live session owns an ordered list of script items. Each item has a stable id, its current text, a revision counter that increases on every text change, and a playback status (待播 / 播放中 / 已播放). The item list is created from the initial script when the session is created, using the shared natural-punctuation segmentation. The item list lives in the backend session, is returned by the session API, and is the single source of truth for what the broadcast reads; the browser does not own an independent editable copy.

## Creating and observing the session

Creating a session accepts the initial script and voice, splits it into items, and returns the session with its item list. Reading the session returns the ordered items with id, text, revision and status, together with the current playback state so the console can render the 实时话术 table and the 当前句 progress.

## Scope of item-level editing

Item-level edit/add/delete during playback is available when the selected engine streams one item per request (the zhubo live path). Engines that synthesize a whole multi-item batch as a single unit (GPT-SoVITS, IndexTTS2) keep their existing batching and cross-sentence prosody; for them the console disables the item edit/add/delete controls and shows a hint, and the whole-script “重新同步脚本” action remains the editing entry. Played-item protection and progress reporting still apply on those engines, but without premature marking of items that have not played yet.

## Editing during playback

Editing an item that is currently playing interrupts that item immediately, discards the remaining audio of the interrupted item and all queued unplayed audio, synthesizes the revised text and plays it from its start, then continues with the following items in order.

Editing a queued (not yet playing) item replaces its text in place, discards any audio already synthesized for the stale text, and plays the item in order when it is reached without interrupting the current playback.

Adding an item inserts it into the list after a chosen item (or at the end) with a new stable id; it plays in order when reached and does not interrupt current playback. Deleting a queued item removes it and discards its audio. Deleting the currently playing item interrupts it and continues with the next item.

## Played-item protection

Once an item has finished playing it can no longer be edited or deleted. The console disables those actions for played rows and shows an explanatory message, and the backend rejects an edit or delete that targets a played item with an explicit error instead of silently applying it.

## Stale-audio discard

After any edit or delete, audio that was synthesized for the replaced or removed text is never played. The browser playback engine tags each synthesis request with the item id and revision it belongs to, and discards any returned or queued audio whose revision is no longer the current revision of that item. No audio belonging to a superseded revision enters the playback queue.

## Whole-script re-sync

The script textbox remains the initial script input. The console's whole-script action re-syncs the textbox content against the backend item list: it computes the differences (added, changed and removed unplayed items) and applies them through the same item semantics above. If applying the differences would change or remove an already-played item, the re-sync is rejected with a clear message and no item is modified.

## Live first-audio latency

The live broadcast must start audible playback without waiting for a whole multi-sentence batch. On the live zhubo path the browser requests one script item at a time and the backend streams that item with the existing natural-punctuation splitter, so the first phrase's audio is returned as soon as it is synthesized and later phrases are generated while the earlier ones play. No special handling is added for the first sentence or first phrase. A warmed session must reach the browser's first audible frame in under 2 seconds for phrase-sized first items; the value grows with the first item's length because one item is returned as one streamed unit when it fits the natural-punctuation splitter's group size. Other providers keep their existing batching and cross-sentence prosody strategy.

## Preserved behavior

Existing behavior is unchanged: selected-provider readiness checks, voice gating, synthesis parameters and audio transport for ordinary and streaming synthesis; start, pause, resume and stop; continuous cancellation; Live2D lip sync driven by the scheduled audio; preview and download; the statistics event path, including the 动态改稿 revision count; and the sessions table script/version/state records.
