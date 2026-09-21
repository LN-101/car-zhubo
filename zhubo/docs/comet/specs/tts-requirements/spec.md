# TTS requirements extraction

## Mandatory extraction

The Chinese Markdown document at whatodo/直播脚本流式 TTS 动态播报模块.md records the supplied DOCX's direct TTS requirements: local file upload and manual frontend text input; audio generation and playback before the full script is synthesized; adding, deleting and editing scripts during unfinished playback with refreshed streaming output; customizable speed, volume and intonation; input-to-first-audio latency <= 3 seconds; smooth playback and a latency report. All mandatory functions must be demonstrable. Acceptance: A1 in brief.md.

## Related requirements

Clearly label voice cloning from small amounts of real speech, reproduction of tone/pauses/emotional rhythm, multiple calm/energetic/approachable voice presets with one-click switching, integration of cloned voices into streaming narration and a subjective naturalness report as related module requirements. Retain vehicle-selection and RAG question-answer context with text and TTS response output. Label sentence segmentation for long automotive scripts, script generation from selling points and duration-related statistics as optional. Do not imply these are independently implemented by this extraction. Acceptance: A2 in brief.md.

## Deliverables

Record architecture and module/dataflow design in PDF/PPT; runnable system, source and deployment instructions including the original local/cloud wording; script streaming, mid-playback editing and related voice/QA demonstrations; dynamic editing and voice optimization technical reports; quantified latency/edit-response tests and related voice evaluation; demonstration video. Record user preferences separately: runnable code first, avoid defensive code and overengineering, optimize performance, integrate the existing index-tts repository into zhubo. Identify unspecified upload formats, edit interruption/replay semantics, parameter ranges and activation timing, benchmark conditions, responsiveness thresholds and voice evaluation details without inventing requirements. Acceptance: A3 in brief.md.
