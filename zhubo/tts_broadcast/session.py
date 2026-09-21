"""Live script scheduling and PCM playback, sharing one lock with edit commands."""
from collections import deque
from dataclasses import dataclass, field
import json
from pathlib import Path
from threading import Condition, Event, Thread
from tempfile import TemporaryFile
from time import perf_counter
from weakref import finalize

import numpy as np
import sounddevice as sd
import soundfile as sf

from .__main__ import split_script
from .engine import Parameters


@dataclass(eq=False)
class Item:
    id: int
    text: str
    played: bool = False
    revision: int = 0


@dataclass(eq=False)
class AudioChunk:
    id: int
    pcm: object
    length: int
    storage_offset: int = None
    spill_pending: bool = False


@dataclass(eq=False)
class Job:
    item: Item
    phrases: list
    revision: int
    next_phrase: int = 0
    chunks: deque = field(default_factory=deque)
    offset: int = 0
    frames: int = 0
    started: bool = False
    suspended: bool = False
    correction: bool = False
    refresh_events: list = field(default_factory=list)
    resume_events: list = field(default_factory=list)

    @property
    def complete(self):
        return self.next_phrase == len(self.phrases) and not self.chunks


class Session:
    sample_rate = 22050

    def __init__(self, text, synthesize, voice, parameters=None, output=None, engine_info=None,
                 capacity=3):
        texts = split_script(text)
        if not texts:
            raise ValueError("请输入非空直播脚本")
        self.condition = Condition()
        self.items = [Item(i + 1, part) for i, part in enumerate(texts)]
        self.next_id = len(self.items) + 1
        self.plan = [self._job(item) for item in self.items]
        self.synthesize = synthesize
        self.voice = voice
        self.parameters = parameters or Parameters()
        self.output = Path(output) if output else None
        self.engine_info = engine_info or {}
        self.capacity = capacity
        self.storage = TemporaryFile()
        self._close_storage = finalize(self, self.storage.close)
        self.started_at = perf_counter()
        self.state = "running"
        self.error = None
        self.finished = Event()
        self.worker = None
        self.first_pcm = None
        self.first_output = None
        self.last_output = None
        self.synthesis_done = None
        self.inference_s = 0.0
        self.generated_frames = 0
        self.underrun_frames = 0
        self.underrun_events = 0
        self.in_gap = False
        self.device_underflows = 0
        self.edits = []
        self.parameter_events = [{"at_s": 0.0, **self.parameters.values()}]
        self.generations = []
        self.playback = []
        self.recording = []
        self.segment_id = 0

    def _job(self, item):
        return Job(item, split_script(item.text), item.revision)

    def _time(self):
        return perf_counter() - self.started_at

    def _item(self, item_id):
        return next(item for item in self.items if item.id == int(item_id))

    def _require_editable(self, item):
        if item.played:
            raise ValueError("该条目已播报，不能修改或删除。请在后续待播条目中修改，或新增话术。")

    def editable_text(self, item_id):
        with self.condition:
            item = self._item(item_id)
            self._require_editable(item)
            return item.text

    def _event(self, kind, item):
        event = {"id": len(self.edits) + 1, "kind": kind, "item_id": item.id,
                 "revision": item.revision, "at_s": self._time(),
                 "regeneration_s": None, "first_output_s": None, "resume_s": None}
        self.edits.append(event)
        return event

    def _spill(self, jobs):
        # The synthesis worker performs storage IO outside the callback lock.
        for job in jobs:
            for chunk in job.chunks:
                if chunk.pcm is not None:
                    chunk.spill_pending = True

    def _synthesis_complete(self):
        if all(j.next_phrase == len(j.phrases) for j in self.plan):
            if self.synthesis_done is None:
                self.synthesis_done = self._time()

    def _drop_lookahead(self):
        # Preserve partially played/suspended jobs exactly; regenerate only unplayed lookahead.
        for job in self.plan:
            if not job.started:
                job.chunks.clear()
                job.offset = 0
                job.next_phrase = 0
                # Replacing the job also invalidates inference currently outside the lock.
                replacement = self._job(job.item)
                replacement.correction = job.correction
                replacement.suspended = job.suspended
                replacement.refresh_events = job.refresh_events
                replacement.resume_events = job.resume_events
                self.plan[self.plan.index(job)] = replacement

    def edit(self, item_id, text):
        if not text.strip():
            raise ValueError("话术不能为空；移除话术请使用删除")
        with self.condition:
            item = self._item(item_id)
            self._require_editable(item)
            item.text = text.strip()
            item.revision += 1
            existing = next((j for j in self.plan if j.item is item), None)
            current = self.plan[0] if self.plan else None
            kind = ("current" if current is not None and existing is current and current.started else
                    "queued" if existing else "text-only")
            event = self._event(kind, item)
            if self.state != "running":
                return event
            replacement = self._job(item)
            replacement.refresh_events.append(event)
            if existing:
                position = self.plan.index(existing)
                replacement.resume_events = existing.resume_events
                replacement.correction = existing.correction
                replacement.suspended = existing.suspended
                self.plan[position] = replacement
                if kind == "current":
                    self._drop_lookahead()
                    if len(self.plan) > 1:
                        self.plan[1].resume_events.append(event)
            self.synthesis_done = None
            self.condition.notify_all()
            return event

    def add(self, text, after_id=None):
        if not text.strip():
            raise ValueError("话术不能为空")
        with self.condition:
            item = Item(self.next_id, text.strip())
            self.next_id += 1
            position = len(self.items) if after_id is None else self.items.index(self._item(after_id)) + 1
            self.items.insert(position, item)
            event = self._event("add", item)
            if self.state == "running":
                job = self._job(item)
                job.refresh_events.append(event)
                # Do not interrupt the active/correction stack; insert before the next queued item.
                following = self.items[position + 1:]
                insertion = next((i for i, j in enumerate(self.plan)
                                  if j.item in following and not j.started), len(self.plan))
                protected = max((i + 1 for i, j in enumerate(self.plan)
                                 if j.started or j.correction or j.suspended), default=0)
                insertion = max(protected, insertion)
                # Keep already-generated audio/parameters when inserting before it.
                # These snapshots rejoin playback when they reach the head, like a resume.
                self._spill(self.plan[insertion:])
                self.plan.insert(insertion, job)
                self.synthesis_done = None
                self.condition.notify_all()
            return item.id

    def delete(self, item_id):
        with self.condition:
            item = self._item(item_id)
            self._require_editable(item)
            event = self._event("delete", item)
            self.items.remove(item)
            removed = [j for j in self.plan if j.item is item]
            current = bool(removed and self.plan[0] in removed)
            old_plan = self.plan
            self.plan = [j for j in old_plan if j.item is not item]
            for job in removed:
                following = next((j for j in old_plan[old_plan.index(job) + 1:] if j in self.plan), None)
                if following:
                    following.resume_events.extend(job.resume_events)
            if self.plan:
                if current:
                    self.plan[0].refresh_events.append(event)
                    self.plan[0].resume_events.append(event)
            elif self.state == "running":
                self.state = "finished"
            self._synthesis_complete()
            self.condition.notify_all()
            return event

    def set_parameters(self, parameters):
        with self.condition:
            self.parameters = parameters
            self.parameter_events.append({"at_s": self._time(), **parameters.values()})
            self.condition.notify_all()

    def stop(self):
        with self.condition:
            self.state = "stopped"
            self.plan.clear()
            self.condition.notify_all()

    def _candidate(self):
        pending = next((j for j in self.plan if any(c.spill_pending for c in j.chunks)), None)
        if pending:
            return pending
        resident = sum(c.pcm is not None for j in self.plan for c in j.chunks)
        if resident >= self.capacity:
            return None
        return next((j for j in self.plan if any(c.pcm is None for c in j.chunks)
                     or j.next_phrase < len(j.phrases)), None)

    def generate_one(self):
        with self.condition:
            if self.state != "running":
                return False
            job = self._candidate()
            if job is None:
                return False
            spilling = next((c for c in job.chunks if c.spill_pending), None)
            saved = next((c for c in job.chunks if c.pcm is None), None)
            if spilling:
                pcm_to_save = spilling.pcm
                storage_offset = spilling.storage_offset
            elif not saved:
                phrase_index = job.next_phrase
                phrase = job.phrases[phrase_index]
                parameters = self.parameters
        if spilling:
            if storage_offset is None:
                self.storage.seek(0, 2)
                storage_offset = self.storage.tell()
                self.storage.write(pcm_to_save.tobytes())
            with self.condition:
                if job in self.plan and spilling in job.chunks:
                    spilling.storage_offset = storage_offset
                    spilling.spill_pending = False
                    if job is not self.plan[0]:
                        spilling.pcm = None
                self.condition.notify_all()
            return True
        if saved:
            self.storage.seek(saved.storage_offset)
            restored = np.frombuffer(self.storage.read(saved.length * 2), dtype=np.int16)
            with self.condition:
                if self.state == "running" and job in self.plan and saved in job.chunks:
                    preceding = self.plan[:self.plan.index(job)]
                    if not any(j.next_phrase < len(j.phrases) or any(c.pcm is None for c in j.chunks)
                               for j in preceding):
                        saved.pcm = restored
                self.condition.notify_all()
            return True
        started = perf_counter()
        pcm = self.synthesize(phrase, parameters, self.voice)
        elapsed = perf_counter() - started
        with self.condition:
            self.inference_s += elapsed
            record = {"id": self.segment_id, "item_id": job.item.id,
                      "revision": job.revision, "phrase": phrase, "at_s": self._time(),
                      "inference_s": elapsed, "audio_s": len(pcm) / self.sample_rate,
                      "parameters": parameters.values(), "discarded": True}
            self.segment_id += 1
            self.generations.append(record)
            self.generated_frames += len(pcm)
            if self.state != "running" or job not in self.plan or job.revision != job.item.revision:
                return True
            record["discarded"] = False
            if self.first_pcm is None:
                self.first_pcm = self._time()
            job.chunks.append(AudioChunk(record["id"], pcm, len(pcm)))
            job.next_phrase += 1
            # An insertion/correction can displace this inference while the lock is released.
            # Spill its result when an earlier job still needs a PCM slot.
            preceding = self.plan[:self.plan.index(job)]
            if any(j.next_phrase < len(j.phrases) or any(c.pcm is None for c in j.chunks)
                   for j in preceding):
                self._spill([job])
            for event in job.refresh_events:
                if event["regeneration_s"] is None:
                    event["regeneration_s"] = self._time() - event["at_s"]
            self._synthesis_complete()
            self.condition.notify_all()
            return True

    def callback(self, outdata, frames, timing, status):
        outdata.fill(0)
        with self.condition:
            if self.state != "running":
                raise sd.CallbackStop
            self.device_underflows += bool(status.output_underflow)
            position = 0
            dac = self._time() + timing.outputBufferDacTime - timing.currentTime
            while position < frames and self.plan:
                job = self.plan[0]
                job.suspended = False
                if not job.chunks or job.chunks[0].pcm is None:
                    break
                chunk = job.chunks[0]
                segment_id, pcm = chunk.id, chunk.pcm
                count = min(frames - position, len(pcm) - job.offset)
                at = dac + position / self.sample_rate
                if self.first_output is None:
                    self.first_output = at
                for event in job.refresh_events:
                    if event["first_output_s"] is None:
                        event["first_output_s"] = at - event["at_s"]
                for event in job.resume_events:
                    if event["resume_s"] is None:
                        event["resume_s"] = at - event["at_s"]
                job.refresh_events.clear()
                job.resume_events.clear()
                if not job.started or not self.playback or self.playback[-1]["segment_id"] != segment_id:
                    self.playback.append({"item_id": job.item.id, "segment_id": segment_id,
                                          "frame": job.frames, "at_s": at})
                outdata[position:position + count, 0] = np.clip(
                    pcm[job.offset:job.offset + count].astype(np.float32) * self.parameters.volume / 100,
                    -32768, 32767).astype(np.int16)
                job.started = True
                job.frames += count
                job.offset += count
                position += count
                self.last_output = dac + position / self.sample_rate
                self.in_gap = False
                if job.offset == len(pcm):
                    job.chunks.popleft()
                    job.offset = 0
                if job.complete:
                    self.plan.pop(0)
                    job.item.played = True
                    if self.plan:
                        self.plan[0].suspended = False
            if position < frames and self.first_output is not None and self.plan:
                self.underrun_frames += frames - position
                if not self.in_gap:
                    self.underrun_events += 1
                    self.in_gap = True
            if self.first_output is not None:
                self.recording.append(outdata.copy())
            self.condition.notify_all()
            if not self.plan:
                self.state = "finished"
                raise sd.CallbackStop

    def start(self):
        self.worker = Thread(target=self._run, name="broadcast", daemon=True)
        self.worker.start()
        return self

    def _run(self):
        try:
            with sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype="int16",
                                 blocksize=512, latency="low", callback=self.callback,
                                 finished_callback=self.finished.set):
                while True:
                    with self.condition:
                        self.condition.wait_for(lambda: self.state != "running" or self._candidate() is not None)
                        if self.state != "running":
                            break
                    self.generate_one()
                self.finished.wait()
        except Exception as error:
            with self.condition:
                self.error = str(error)
                self.state = "error"
                self.plan.clear()
                self.condition.notify_all()
        finally:
            self.finished.set()
            self.save()
            self._close_storage()

    def snapshot(self):
        with self.condition:
            now = self.plan[0].item.id if self.plan else None
            return {"state": self.state, "error": self.error, "now_playing": now,
                    "items": [{"id": item.id, "text": item.text, "revision": item.revision,
                               "status": "播放中" if item.id == now else "已播放" if item.played else "待播放"}
                              for item in self.items],
                    "parameters": self.parameters.values(), "parameter_events": list(self.parameter_events),
                    "voice": self.voice, "environment": self.engine_info,
                    "measurement": "PortAudio DAC timestamps; not acoustic capture. WAV includes callback gaps and applied volume.",
                    "first_pcm_s": self.first_pcm, "first_device_output_s": self.first_output,
                    "first_output_within_3s": self.first_output is not None and self.first_output <= 3,
                    "synthesis_wall_s": self.synthesis_done,
                    "streamed_before_synthesis_done": (self.first_output < self.synthesis_done
                        if self.first_output is not None and self.synthesis_done is not None else None),
                    "audio_s": self.generated_frames / self.sample_rate,
                    "rtf": self.inference_s / (self.generated_frames / self.sample_rate) if self.generated_frames else None,
                    "playback_s": self.last_output - self.first_output if self.last_output is not None else None,
                    "underrun_events": self.underrun_events,
                    "underrun_s": self.underrun_frames / self.sample_rate,
                    "device_underflows": self.device_underflows,
                    "edits": [dict(e) for e in self.edits],
                    "generations": list(self.generations), "playback": list(self.playback),
                    "output": str(self.output) if self.output else None}

    def save(self):
        if self.output:
            self.output.mkdir(parents=True, exist_ok=True)
            (self.output / "metrics.json").write_text(
                json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
            if self.recording:
                sf.write(self.output / "playback.wav", np.concatenate(self.recording), self.sample_rate,
                         subtype="PCM_16")
