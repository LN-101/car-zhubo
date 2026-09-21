import unittest
from types import SimpleNamespace
from threading import Thread

import numpy as np
import sounddevice as sd

from tts_broadcast.__main__ import split_script
from tts_broadcast.playback import Player, Segment


class StreamingTests(unittest.TestCase):
    def render(self, player, frames):
        out = np.empty((frames, 1), dtype=np.int16)
        timing = SimpleNamespace(outputBufferDacTime=1.01, currentTime=1.0)
        player.callback(out, frames, timing, SimpleNamespace(output_underflow=False))
        return out[:, 0]

    def test_split_preserves_content_and_decimals(self):
        text = "欢迎来到直播间。轴距2.72米，电池58.3千瓦时！" * 8
        pieces = split_script(text)
        self.assertEqual("".join(pieces), text)
        self.assertLessEqual(len(pieces[0]), 16)
        self.assertTrue(any("58.3" in part for part in pieces))

    def test_callback_crosses_segment_boundary_in_order(self):
        player = Player()
        player.put(Segment(0, "a", np.array([1, 2], dtype=np.int16)))
        player.put(Segment(1, "b", np.array([3, 4, 5], dtype=np.int16)))
        np.testing.assert_array_equal(self.render(player, 4), [1, 2, 3, 4])
        self.assertEqual(player.played_ids, [0, 1])
        self.assertEqual(player.underrun_frames, 0)

    def test_decimal_crossing_hard_boundary(self):
        text = "欢迎了解这款汽车搭载电池容量58.3千瓦时。"
        pieces = split_script(text)
        self.assertEqual("".join(pieces), text)
        self.assertTrue(any("58.3" in part for part in pieces))
        number = "123456789012345678.90"
        self.assertEqual(split_script(number + "公里。"), [number + "公里。"])

    def test_natural_boundaries_replace_character_limits(self):
        sentence = "我们继续看看它的空间和日常使用体验。"
        long_phrase = "这是一段超过三十二个字符但中间没有任何标点而且应该完整送入语音合成的汽车介绍。"
        for text in (sentence, long_phrase, long_phrase.rstrip("。")):
            with self.subTest(text=text):
                self.assertEqual(split_script(text), [text])
                self.assertEqual([part for piece in split_script(text)
                                  for part in split_script(piece)], [text])
        text = "欢迎。开始。" + sentence + long_phrase + "轴距2.72米，续航58.3公里！"
        pieces = split_script(text)
        self.assertEqual("".join(pieces), text)
        self.assertEqual(pieces[0], "欢迎。开始。")
        self.assertIn(sentence, pieces)
        self.assertIn(long_phrase, pieces)
        self.assertTrue(all(piece[-1] in "。，！" for piece in pieces))
        self.assertEqual(split_script(" \n\t"), [])
        self.assertEqual(split_script("  欢迎。  "), ["欢迎。"])

    def test_underrun_and_recovery(self):
        player = Player()
        self.render(player, 4)
        self.assertEqual(player.underrun_events, 0)
        player.put(Segment(0, "a", np.ones(2, dtype=np.int16)))
        self.render(player, 4)
        self.render(player, 4)
        self.assertEqual(player.underrun_events, 1)
        self.assertEqual(player.underrun_frames, 6)
        player.put(Segment(1, "b", np.ones(2, dtype=np.int16)))
        self.render(player, 4)
        self.assertEqual(player.underrun_events, 2)

    def test_cancel_unblocks_producer_and_discards_audio(self):
        player = Player(capacity=1)
        segment = Segment(0, "a", np.ones(2, dtype=np.int16))
        player.put(segment)
        result = []
        producer = Thread(target=lambda: result.append(player.put(segment)))
        producer.start()
        player.cancel()
        producer.join(timeout=1)
        self.assertEqual(result, [False])
        self.assertFalse(player.queue)
        with self.assertRaises(sd.CallbackStop):
            self.render(player, 4)

    def test_finished_tail_not_counted_as_underrun(self):
        player = Player()
        player.put(Segment(0, "a", np.ones(2, dtype=np.int16)))
        player.finish()
        with self.assertRaises(sd.CallbackStop):
            self.render(player, 4)
        self.assertEqual(player.underrun_frames, 0)


if __name__ == "__main__":
    unittest.main()
