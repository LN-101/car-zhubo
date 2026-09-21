# Outcome

Implement the user-approved first milestone: runnable command-line streaming speech using /home/ln/AI/index-tts, concurrent generation and continuous local playback, and actual latency measurements. The requirements extraction is already complete.

# Scope

Preserve the source requirements extraction and implement text/file CLI input, sentence-based synthesis, local playback, cancellation and segment identity foundations, and a reproducible benchmark report. Use the new resource files only as reference samples. They were read completely; inconsistent pricing is excluded from the demo. This milestone evaluates the <=3 second target honestly, rather than claiming it without measurement.

## Source coverage

Source: whatodo/汽车直播智能体设计与实现.docx. All 52 body paragraphs read; no tables, drawings or external links; footnotes and endnotes contain no text. Paragraph numbering follows document XML order. All units below have complete read status. Spec reference: specs/tts-requirements/spec.md.

| Source unit | Read | Retained semantics | Coverage | Spec / acceptance | Reason |
| --- | --- | --- | --- | --- | --- |
| P1–3 | complete | Competition identity and title | background | - | Source identity |
| P4–6 | complete | Industry context, voice and script limitations | background | - | Motivation |
| P7–10 | complete | Competition objectives | background | - | Educational and business context |
| P11–14 | complete | Entrants and team rules | non-goal | - | Not TTS behavior |
| P15–19 | complete | Overall automotive agent context | background | - | Overall system motivation |
| P20–21 | complete | Mandatory functions must be demonstrable | covered | Spec: Mandatory extraction / A1 | Retained as demonstration constraint |
| P22–26 | complete | RAG uploads, indexing, CRUD, provenance, 85% accuracy and 40 samples | non-goal | - | Separate RAG module; upload formats not inherited by TTS |
| P27–28 | complete | File and text input | covered | Spec: Mandatory extraction / A1 | Direct TTS requirement |
| P29 | complete | Generate and play before full synthesis | covered | Spec: Mandatory extraction / A1 | Direct TTS requirement |
| P30 | complete | Add, delete and edit during playback; refresh audio | covered | Spec: Mandatory extraction / A1 | Direct TTS requirement |
| P31 | complete | Speed, volume, intonation; first audio within 3 seconds; smooth playback; latency report | covered | Spec: Mandatory extraction / A1 | Direct TTS requirement |
| P32–35 | complete | Clone samples, voice presets, streaming integration, subjective evaluation | covered | Spec: Related requirements / A2 | Record dependency without silently expanding implementation |
| P36–38 | complete | Vehicle selection and RAG answers with text and speech | covered | Spec: Related requirements / A2 | Record upstream context and TTS integration |
| P39–40 | complete | Optional sentence segmentation optimization | covered | Spec: Related requirements / A2 | Explicitly optional |
| P41 | complete | Optional script generation from vehicle selling points | covered | Spec: Related requirements / A2 | Upstream optional feature |
| P42 | complete | Optional duration, vehicle inquiry and retrieval statistics | covered | Spec: Related requirements / A2 | Duration related to broadcasting |
| P43 | complete | Optional data compliance plan | non-goal | - | Not a TTS extraction requirement |
| P44–45 | complete | Architecture and design PDF/PPT | covered | Spec: Deliverables / A3 | Extract TTS portion |
| P46 | complete | Runnable system, local/cloud demonstration, source and deployment instructions | covered | Spec: Deliverables / A3 | Extract TTS and integration demonstrations |
| P47 | complete | Technical reports for RAG, dynamic TTS editing and voice cloning | covered | Spec: Deliverables / A3 | Extract TTS and voice reports; RAG report out of scope |
| P48 | complete | Quantified functional tests and samples | covered | Spec: Deliverables / A3 | Extract latency, editing responsiveness and voice-related metrics |
| P49 | complete | Full demonstration video | covered | Spec: Deliverables / A3 | Extract TTS demonstrations |
| P50 | complete | Optional business plan | non-goal | - | Not TTS requirements |
| P51–52 | complete | Company-provided vehicle and promotional materials | background | - | Supporting resources |

# Non-goals

No RAG, clone training, frontend, live script editing or speech parameter UI in this milestone. These remain future module requirements. Model loading is measured separately from warm-request latency. Physical acoustic latency cannot be claimed from software timestamps alone.

# Acceptance examples

- A1: The extraction preserves all direct mandatory TTS requirements and the live demonstration obligation, including the exact latency threshold of <= 3 seconds.
- A2: Voice cloning, presets, question-answer speech and optional segmentation/script/statistics requirements are distinguished from direct TTS requirements.
- A3: TTS delivery documents and tests are included; user constraints and unspecified implementation details are clearly identified.
- A4: Real IndexTTS 2.5 weights produce nonempty audible PCM from a Chinese automotive script, with both CLI text and UTF-8 file input supported.
- A5: A multi-segment script starts playback before synthesis completes, plays segments in order while synthesis continues, and records actual underruns without hiding them. Segment identifiers and cancellation prevent future queued audio from playing after cancellation.
- A6: A reproducible report records environment, initialization and warmup conditions, first PCM latency, audio-device playback timing, synthesis real-time factor and underrun data, explicitly evaluating the <=3 second target.

# Constraints and invariants

User preference: prioritize runnable code, avoid defensive code and overengineering, pursue maximum practical performance. Use /home/ln/AI/index-tts and integrate into /home/ln/AI/zhubo. Saved as project memory. Formal Native artifacts follow configured English; requested extraction follows the Chinese source.

# Decisions

The user approved the first milestone after the proposed three steps (real inference, segmented continuous playback, latency measurement), then explicitly requested completion with the new resources. Use the current workspace, existing virtual environment and IndexTTS 2.5 BF16 inference. Keep one tightly coupled change. Use an included reference voice; use automotive reference material without contradictory prices. Implement a CLI first because no application currently exists. Avoid unnecessary services and abstractions.

# Open questions

No unresolved questions for the approved first milestone. Full dynamic editing semantics remain deferred to the next milestone.

# Verification expectations

Check extraction coverage, focused segment/playback/cancellation tests, and real GPU inference with local audio playback. Record measured limitations. Independent review and verification assess A1-A6.
