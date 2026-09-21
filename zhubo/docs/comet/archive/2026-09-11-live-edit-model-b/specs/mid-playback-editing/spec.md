# Mid-playback script editing

## Script model and playback order

A broadcast owns an ordered list of script items with stable identities. Playback follows the list order, and synthesis runs ahead of playback inside the existing bounded queue. Item operations are applied atomically and serialized with playback, and text is never silently dropped. Acceptance: A2, A3, A5.

## Editing the currently playing item

Editing the item that is being played interrupts it immediately: the remaining audio of that item and all queued unplayed audio are discarded, the fixed text is synthesized and plays from its start, and playback then continues with the following items in order. Acceptance: A2, A3.

## Queued and played items

Editing a queued (not yet playing) item replaces its text in place; any audio already synthesized for the stale text is discarded, and the item plays in order when reached without interrupting current playback. Adding an item inserts it into the list at the chosen position, and it plays in order when reached. Acceptance: A2, A3.

## Correcting an already-played item

While the broadcast is unfinished, editing an item that has already finished playing interrupts current playback immediately, synthesizes and plays the corrected item in full, then resumes the interrupted position from the exact interruption point: an interrupted item continues from where it stopped without repeating audio, and an interruption exactly at an item boundary continues with the next item in order. Nested interruptions resume in reverse order, so content interrupted earlier continues after the newer correction finishes. Once the broadcast has finished, editing a played item only updates the item text and replays nothing. Acceptance: A2, A3.

## Deleting items

Deleting a queued item removes it and discards its audio. Deleting the currently playing item interrupts playback immediately and continues with the next item. Deleting a played item removes it from the list with no replay. Acceptance: A2, A3.

## Refresh and timing evidence

After any edit, no audio synthesized for the replaced text is heard; its queued audio is discarded rather than played. For every edit the session records its kind, target item and time, with response timing: for interrupt and correction edits, from the control action to the first refreshed or corrected device output and to the resumed playback position; for queued edits, from the control action to regeneration of the updated item. Acceptance: A3, A6.
