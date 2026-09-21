from collections import deque
from dataclasses import dataclass
from threading import Condition, Event
from time import perf_counter

import numpy as np
import sounddevice as sd


@dataclass
class Segment:
    id: int
    text: str
    pcm: np.ndarray


class Player:
    def __init__(self, sample_rate=22050, capacity=3):
        self.sample_rate = sample_rate
        self.capacity = capacity
        self.queue = deque()
        self.condition = Condition()
        self.finished = Event()
        self.cancelled = Event()
        self.done = False
        self.offset = 0
        self.started = False
        self.first_output_at = None
        self.last_output_at = None
        self.underrun_frames = 0
        self.underrun_events = 0
        self.device_underflows = 0
        self.in_gap = False
        self.played_ids = []

    def put(self, segment):
        with self.condition:
            self.condition.wait_for(
                lambda: len(self.queue) < self.capacity or self.cancelled.is_set()
            )
            if self.cancelled.is_set():
                return False
            self.queue.append(segment)
            return True

    def finish(self):
        with self.condition:
            self.done = True

    def cancel(self):
        with self.condition:
            self.cancelled.set()
            self.queue.clear()
            self.offset = 0
            self.condition.notify_all()

    def callback(self, outdata, frames, timing, status):
        outdata.fill(0)
        with self.condition:
            if self.cancelled.is_set():
                raise sd.CallbackStop
            self.device_underflows += bool(status.output_underflow)
            position = 0
            while position < frames and self.queue:
                segment = self.queue[0]
                if self.offset == 0:
                    self.played_ids.append(segment.id)
                count = min(frames - position, len(segment.pcm) - self.offset)
                if self.first_output_at is None:
                    self.first_output_at = perf_counter() + (
                        timing.outputBufferDacTime - timing.currentTime
                    ) + position / self.sample_rate
                outdata[position:position + count, 0] = segment.pcm[
                    self.offset:self.offset + count
                ]
                self.started = True
                self.in_gap = False
                position += count
                self.offset += count
                self.last_output_at = perf_counter() + (
                    timing.outputBufferDacTime - timing.currentTime
                ) + position / self.sample_rate
                if self.offset == len(segment.pcm):
                    self.queue.popleft()
                    self.offset = 0
                    self.condition.notify_all()
            if position < frames and self.started and not self.done:
                self.underrun_frames += frames - position
                if not self.in_gap:
                    self.underrun_events += 1
                    self.in_gap = True
            if self.done and not self.queue:
                raise sd.CallbackStop

    def open(self):
        return sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=512,
            latency="low",
            callback=self.callback,
            finished_callback=self.finished.set,
        )
