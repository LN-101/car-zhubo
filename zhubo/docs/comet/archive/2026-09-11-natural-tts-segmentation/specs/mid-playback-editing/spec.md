# Mid-playback script editing

## Script model and playback order

A broadcast owns an ordered list of script items with stable identities. Playback follows the list order, and synthesis runs ahead of playback inside the existing bounded queue. Item operations are applied atomically and serialized with playback, and text is never silently dropped. For correction-return behavior, a paragraph means a complete script item displayed as one row in the Web script table, including all of its synthesis phrases.

## Editing the currently playing item

Editing the item that is being played interrupts it immediately: the remaining audio of that item and all queued unplayed audio are discarded, the fixed text is synthesized and plays from its start, and playback then continues with the following items in order.

## Queued and played items

Editing a queued (not yet playing) item replaces its text in place; any audio already synthesized for the stale text is discarded, and the item plays in order when reached without interrupting current playback. Adding an item inserts it into the list at the chosen position, and it plays in order when reached.

## Correcting an already-played item

While the broadcast is unfinished, editing an item that has already finished playing interrupts current playback immediately, synthesizes and plays the corrected item in full, then returns to the interrupted script item and restarts that item from its beginning. Previously played audio within the interrupted item is intentionally repeated, including earlier synthesis phrases whose buffers have been consumed. For example, after A completed and B partially played, correcting A produces corrected A in full, then full B from its start, then C in normal order. The Web explanation clearly describes this paragraph-start return. Acceptance: A5 in brief.md.

An interruption exactly at an item boundary continues with the next item from its beginning. Nested interruptions return in reverse order, restarting each interrupted item from its own beginning after the newer correction finishes. Once the broadcast has finished, editing a played item only updates the item text and replays nothing. Keep bounded resident audio during repeated corrections; do not retain the entire broadcast PCM in memory to implement replay. Queued edits, insertion and cancellation retain their existing behavior. Acceptance: A6 in brief.md.

## Deleting items

Deleting a queued item removes it and discards its audio. Deleting the currently playing item interrupts playback immediately and continues with the next item. Deleting a played item removes it from the list with no replay.

## Refresh and timing evidence

After any edit, no audio synthesized for the replaced text is heard; its queued audio is discarded rather than played. For every edit the session records its kind, target item and time, with response timing: for interrupt and correction edits, from the control action to the first refreshed or corrected device output and to the resumed playback position; for queued edits, from the control action to regeneration of the updated item. Return timing refers to first output of the restarted item. Interruption metadata retains the actual position at which playback was interrupted, rather than reporting the restart position as the original interruption.
