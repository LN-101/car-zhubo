# Outcome

Prevent application-level character limits from splitting Chinese speech inside words, including the reported split between 体 and 验 in 我们继续看看它的空间和日常使用体验。. After correcting an already-played item, restart the interrupted script item from its beginning when returning to it.

# Scope

Update the shared script segmentation used by CLI broadcast and Web sessions, including initial jobs, edits and insertions. Retain natural punctuation boundaries and short-phrase grouping, treating the existing 16/32 character targets as soft grouping targets rather than hard slicing limits. Change correction-return behavior to restart the interrupted paragraph (the full script item shown as one Web table row), including nested corrections. Update the relevant UI explanation and focused regression coverage.

# Non-goals

No upstream IndexTTS changes, model retraining, new tokenizer or dependency, generation-warning cleanup, playback scheduler redesign, UI redesign, or universal guarantee of natural prosody for arbitrarily long unpunctuated input.

# Acceptance examples

- A1: Splitting 我们继续看看它的空间和日常使用体验。 returns that complete phrase as one segment; splitting it again also keeps it complete.
- A2: For phrases longer than either grouping target, application segments end only at existing natural punctuation or end of input; a long unpunctuated phrase is retained without character slicing. Short adjacent phrases may still be grouped using the existing first/later targets.
- A3: Segmentation preserves spoken content and punctuation in order, keeps decimal numbers such as 58.3 intact, and retains empty/whitespace-input handling and existing boundary-whitespace trimming.
- A4: Web initial synthesis and newly edited or inserted text submit the reported phrase intact to the synthesis function, with no standalone 验。 task. Existing playback, cancellation, edit and parameter tests continue to pass except assertions intentionally superseded by A5/A6.
- A5: When A has finished and B is partially playing, editing A immediately plays corrected A in full, then restarts the full B script item from its beginning before continuing to C. This includes B containing multiple synthesis phrases whose earlier audio has already been consumed. The Web explanation states that return restarts the original paragraph.
- A6: Nested corrections return in reverse interruption order and restart each interrupted item from its beginning. An interruption at an item boundary starts the next item normally. Editing after broadcast completion remains text-only; queued edits, inserts and cancellation retain their existing behavior, and correction playback retains bounded resident audio.

# Constraints and invariants

Use the current directory /home/ln/AI/zhubo and branch feature/new-model-impl; preserve the unrelated untracked .codegraph/ directory. Continue using the existing IndexTTS integration and its 120-token per-segment setting for model-side long-input handling. Preserve streaming playback and bounded lookahead. Longer intact phrases may increase first-audio latency; measure the reported phrase when the model environment is usable and do not claim acoustic validation from unit tests.

# Decisions

- The user selected option 1: current-directory development, without a new branch or worktree.
- The reported log was supplied as debugging evidence, not a source requirements document.
- Inspection reproduced the exact split in the shared split_script function before model inference. Web job creation invokes the same splitter again.
- Proposed final behavior: natural punctuation defines application splitting boundaries; 16/32 character targets guide grouping only. IndexTTS retains its own token segmentation for unusually long phrases.
- The user confirmed the original segmentation scope and added paragraph-start replay after correcting already-played content.
- Paragraph means the full script item displayed as one Web table row, not an internal synthesis chunk. Example: A completed, B half played, edit A -> corrected A -> B from its beginning -> C. Nested corrections apply the same return rule in reverse order.
- Keep one Native change: segmentation and paragraph restart affect the same session text/audio flow and need joint regression coverage; no Supervisor decomposition is needed.

# Open questions

None. The expanded scope and behavior await the Runtime final Shape confirmation.

# Verification expectations

Run focused split and session tests plus the existing unit suite. Include correction-return PCM ordering, a multi-phrase interrupted item with already-consumed audio, nested interruptions, exact item boundaries, completed sessions and bounded memory. Include the exact reported sentence, repeated splitting, phrases above 16 and 32 characters, punctuation, decimals, empty input, and synthesis-call capture through Web creation/edit/insertion. Inspect model integration for unchanged token-limit handling. If real model synthesis is available, record its actual phrase input, generated audio and timing; distinguish automated text correctness from subjective listening and document unavailable checks. A fresh independent review and Verifier are required by Native when the platform can supply them.
