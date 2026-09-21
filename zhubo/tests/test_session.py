import tempfile
import unittest
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

import numpy as np
import sounddevice as sd

from tts_broadcast.engine import Parameters
from tts_broadcast.session import Session


class SessionTests(unittest.TestCase):
    def session(self):
        def synthesize(text, parameters, voice):
            start = {"甲。": 10, "乙。": 20, "丙。": 30, "丁。": 40, "改。": 50, "新。": 60}[text]
            return np.arange(start, start + 6, dtype=np.int16)
        # Use explicit line-sized items; split_script normally combines short phrases.
        session = Session("甲。", synthesize, "voice")
        session.add("乙。")
        session.add("丙。")
        session.edits.clear()
        for job in session.plan:
            job.refresh_events.clear()
        return session

    def render(self, session, frames):
        data = np.zeros((frames, 1), dtype=np.int16)
        timing = SimpleNamespace(outputBufferDacTime=1.01, currentTime=1.0)
        try:
            session.callback(data, frames, timing, SimpleNamespace(output_underflow=False))
        except sd.CallbackStop:
            pass
        return data[:, 0]

    def fill(self, session):
        while session.generate_one():
            pass

    def test_bounded_queue_and_order(self):
        session = self.session()
        session.add("丁。")
        self.fill(session)
        self.assertEqual(len(session.generations), 3)
        np.testing.assert_array_equal(self.render(session, 8), [10, 11, 12, 13, 14, 15, 20, 21])
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 16), [22, 23, 24, 25, 30, 31, 32, 33, 34, 35, 40, 41, 42, 43, 44, 45])
        self.assertEqual(session.state, "finished")
        self.assertEqual(session.underrun_frames, 0)

    def test_current_edit_discards_stale_and_restarts(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        event = session.edit(1, "改。")
        np.testing.assert_array_equal(self.render(session, 2), [0, 0])
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 8), [50, 51, 52, 53, 54, 55, 20, 21])
        self.assertIsNotNone(event["first_output_s"])
        self.assertIsNotNone(event["resume_s"])
        self.assertEqual(session.underrun_frames, 2)

    def test_played_items_rejected_without_changing_playback(self):
        for frames in (6, 8, 18):
            for operation in ("edit", "delete", "editable_text"):
                with self.subTest(frames=frames, operation=operation):
                    session = self.session()
                    self.fill(session)
                    self.render(session, frames)
                    before = session.snapshot()
                    plan = list(session.plan)
                    args = (1, "改。") if operation == "edit" else (1,)
                    with self.assertRaisesRegex(ValueError, "请在后续待播条目中修改"):
                        getattr(session, operation)(*args)
                    self.assertEqual(session.snapshot(), before)
                    self.assertEqual(session.plan, plan)
                    if frames < 18:
                        np.testing.assert_array_equal(self.render(session, 18 - frames),
                                                      (list(range(10, 16)) + list(range(20, 26))
                                                       + list(range(30, 36)))[frames:])

    def test_reported_sentence_reaches_synthesis_intact(self):
        sentence = "我们继续看看它的空间和日常使用体验。"
        for operation in ("initial", "edit", "add"):
            with self.subTest(operation=operation):
                calls = []
                def synthesize(text, *args):
                    calls.append(text)
                    return np.ones(6, dtype=np.int16)
                session = Session(sentence if operation == "initial" else "欢迎。", synthesize, "voice")
                if operation == "edit":
                    session.edit(1, sentence)
                elif operation == "add":
                    session.add(sentence)
                self.fill(session)
                self.assertEqual(calls.count(sentence), 1)
                self.assertNotIn("验。", calls)

    def test_queued_edit_and_insert_leave_current_uninterrupted(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        event = session.edit(2, "改。")
        session.add("新。", after_id=1)
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 4), [12, 13, 14, 15])
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 12), [60, 61, 62, 63, 64, 65, 50, 51, 52, 53, 54, 55])
        self.assertIsNotNone(event["regeneration_s"])

    def test_append_preserves_queued_pcm_and_parameters(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        queued = [job.chunks[0].pcm for job in session.plan[1:]]
        session.set_parameters(Parameters(2, 100, "warm", 1))
        session.add("丁。")
        self.assertIs(session.plan[1].chunks[0].pcm, queued[0])
        self.assertIs(session.plan[2].chunks[0].pcm, queued[1])
        self.assertEqual(len(session.generations), 3)
        self.assertEqual([g["parameters"]["speed"] for g in session.generations], [1, 1, 1])
        np.testing.assert_array_equal(self.render(session, 16), [12, 13, 14, 15, 20, 21, 22, 23, 24, 25, 30, 31, 32, 33, 34, 35])
        self.fill(session)
        self.assertEqual(session.generations[-1]["parameters"]["speed"], 2)

    def test_insert_before_full_queue_preserves_prepared_audio(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        old = session.plan[1].chunks[0]
        session.add("新。", after_id=1)
        self.fill(session)
        self.assertIs(session.plan[2].chunks[0], old)
        np.testing.assert_array_equal(self.render(session, 16), [12, 13, 14, 15, 60, 61, 62, 63, 64, 65, 20, 21, 22, 23, 24, 25])

    def test_repeated_insertions_keep_pcm_memory_bounded(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        for _ in range(12):
            session.add("新。", after_id=1)
            self.fill(session)
            self.assertLessEqual(sum(c.pcm is not None for j in session.plan for c in j.chunks), 3)
        output = []
        while session.state == "running":
            self.fill(session)
            output.extend(self.render(session, 1))
        self.assertEqual(output, [12, 13, 14, 15] + list(range(60, 66)) * 12
                         + list(range(20, 26)) + list(range(30, 36)))

    def test_insert_during_inflight_generation_with_one_slot(self):
        session = self.session()
        session.capacity = 1
        session.generate_one()
        self.render(session, 6)
        entered, release = Event(), Event()
        original = session.synthesize
        def delayed(*args):
            entered.set()
            release.wait(2)
            return original(*args)
        session.synthesize = delayed
        worker = Thread(target=session.generate_one)
        worker.start()
        self.assertTrue(entered.wait(1))
        session.add("新。", after_id=1)
        release.set()
        worker.join(2)
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 6), list(range(60, 66)))
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 6), list(range(20, 26)))

    def test_storage_stall_does_not_block_resident_playback(self):
        for operation in ("write", "read"):
            with self.subTest(operation=operation):
                session = self.session()
                self.fill(session)
                self.render(session, 1)
                session.add("新。", after_id=1)
                if operation == "read":
                    session.generate_one()  # Spill B.
                    session.generate_one()  # Spill C.
                    session.generate_one()  # Generate the inserted item.
                entered, release, rendered = Event(), Event(), Event()
                original = session.storage
                class SlowStorage:
                    def __getattr__(self, name):
                        method = getattr(original, name)
                        if name != operation:
                            return method
                        def delayed(*args):
                            entered.set()
                            release.wait(2)
                            return method(*args)
                        return delayed
                session.storage = SlowStorage()
                io = Thread(target=session.generate_one)
                io.start()
                self.assertTrue(entered.wait(1))
                output = []
                def render():
                    output.extend(self.render(session, 2))
                    rendered.set()
                audio = Thread(target=render)
                audio.start()
                try:
                    self.assertTrue(rendered.wait(0.2), "storage IO blocked the callback lock")
                finally:
                    release.set()
                    io.join(2)
                    audio.join(2)
                self.assertEqual(output, [11, 12])

    def test_delete_unsynthesized_tail_completes_synthesis_metrics(self):
        session = self.session()
        last = session.add("丁。")
        self.fill(session)
        self.assertIsNone(session.synthesis_done)
        self.render(session, 2)
        session.delete(last)
        self.assertIsNotNone(session.synthesis_done)
        self.render(session, 16)
        self.assertIsNotNone(session.snapshot()["streamed_before_synthesis_done"])

    def test_delete_current_queued_and_played(self):
        session = self.session()
        self.fill(session)
        self.render(session, 2)
        session.delete(1)
        session.delete(3)
        np.testing.assert_array_equal(self.render(session, 6), [20, 21, 22, 23, 24, 25])
        with self.assertRaisesRegex(ValueError, "已播报"):
            session.delete(2)
        self.assertEqual([item.id for item in session.items], [2])

    def test_delete_only_item_finishes_and_wakes_worker(self):
        session = Session("甲。", lambda *args: np.ones(6, dtype=np.int16), "voice")
        session.generate_one()
        self.render(session, 2)
        session.delete(1)
        self.assertEqual(session.state, "finished")
        self.assertFalse(session.plan)
        self.assertFalse(session.generate_one())
        np.testing.assert_array_equal(self.render(session, 2), [0, 0])

    def test_inflight_stale_generation_discarded(self):
        session = self.session()
        entered, release = Event(), Event()
        original = session.synthesize
        def delayed(*args):
            entered.set()
            release.wait(2)
            return original(*args)
        session.synthesize = delayed
        worker = Thread(target=session.generate_one)
        worker.start()
        self.assertTrue(entered.wait(1))
        session.edit(1, "改。")
        release.set()
        worker.join(2)
        self.assertTrue(session.generations[0]["discarded"])
        self.fill(session)
        np.testing.assert_array_equal(self.render(session, 6), [50, 51, 52, 53, 54, 55])

    def test_hybrid_parameters_and_clipping(self):
        session = self.session()
        session.synthesize = lambda *args: np.array([20000, -20000, 100], np.int16)
        session.generate_one()
        session.set_parameters(Parameters(2, 200, "warm", 0.5))
        session.generate_one()
        np.testing.assert_array_equal(self.render(session, 2), [32767, -32768])
        session.set_parameters(Parameters(0.5, 0, "steady", 1))
        np.testing.assert_array_equal(self.render(session, 2), [0, 0])
        self.assertEqual(session.generations[0]["parameters"]["duration_factor"], 1)
        self.assertEqual(session.generations[1]["parameters"]["duration_factor"], 0.5)
        self.assertEqual(session.generations[1]["parameters"]["emo_vector"], [0.225, 0, 0, 0, 0, 0, 0, 0.175])
        for args in [(0, 100, "neutral", 0), (1, 201, "neutral", 0), (1, 100, "bad", 0), (1, 100, "warm", 2)]:
            with self.assertRaises(ValueError):
                Parameters(*args)

    def test_finish_edit_no_replay_stop_and_report(self):
        session = self.session()
        self.fill(session)
        self.render(session, 20)
        self.assertEqual(session.underrun_frames, 0)
        with self.assertRaisesRegex(ValueError, "已播报"):
            session.edit(1, "改。")
        self.assertFalse(session.plan)
        with tempfile.TemporaryDirectory() as directory:
            session.output = Path(directory)
            session.save()
            self.assertTrue((session.output / "metrics.json").exists())
            self.assertTrue((session.output / "playback.wav").exists())
        session = self.session()
        self.fill(session)
        session.stop()
        np.testing.assert_array_equal(self.render(session, 2), [0, 0])
        self.assertFalse(session.generate_one())


if __name__ == "__main__":
    unittest.main()
