from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from coldcamera.application import Application
from coldcamera.classes.pipeline import ProcessingPipeline
from coldcamera.core.media_service import MediaService
from coldcamera.core.media_sources import MemoryFrameSource, VideoFrameSource
from coldcamera.core.operations import CancellationToken, OperationCancelled
from coldcamera.core.pipeline_snapshot import PipelineSnapshot
from coldcamera.effects.descriptors import EFFECT_DESCRIPTORS
from coldcamera.effects.includes.exposure import ExposureEffect


class BackendBoundaryTests(unittest.TestCase):
    def make_application(self) -> Application:
        with patch("coldcamera.application.initialize_logger"):
            return Application()

    def test_application_import_does_not_import_qt(self) -> None:
        command = "import sys, coldcamera.application, coldcamera.core.media_service, coldcamera.effects.descriptors; assert not any(name == 'PySide6' or name.startswith('PySide6.') for name in sys.modules)"
        result = subprocess.run([sys.executable, "-c", command], capture_output=True, text=True, check=False, env={**os.environ, "PYTHONPATH": str(Path.cwd())})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failed_open_preserves_active_media(self) -> None:
        app = self.make_application()
        existing = MemoryFrameSource("existing.png", "image", [np.zeros((2, 2, 4), dtype=np.uint8)], 1)
        app.set_media(existing)

        with patch.object(MediaService, "load_source", side_effect=ValueError("bad image")):
            with self.assertRaisesRegex(ValueError, "bad image"):
                app.open_media("bad.png", "image")

        self.assertIs(app.snapshot().media, existing)

    def test_pipeline_snapshot_is_detached_and_preserves_enabled_state(self) -> None:
        effect = ExposureEffect()
        effect.set_parameter("exposure", 1.5)
        effect.enabled = False
        pipeline = ProcessingPipeline([effect])
        snapshot = PipelineSnapshot.from_pipeline(pipeline)

        effect.set_parameter("exposure", 0.5)
        restored = snapshot.build_pipeline()
        self.assertEqual(restored.effects[0].get_parameter("exposure"), 1.5)
        self.assertFalse(restored.effects[0].enabled)

    def test_each_effect_parameter_has_a_separate_editor_descriptor(self) -> None:
        descriptors = [descriptor for group in EFFECT_DESCRIPTORS.values() for descriptor in group.values()]
        self.assertEqual(len(descriptors), 23)
        for descriptor in descriptors:
            effect = descriptor.effect_class()
            parameter_names = {name for name, _parameter in effect.params}
            editor_names = {element["name"] for element in descriptor.editor_elements if "name" in element}
            self.assertEqual(editor_names, parameter_names, descriptor.name)

    def test_task_snapshot_keeps_old_media_after_session_replacement(self) -> None:
        app = self.make_application()
        original = np.full((2, 2, 4), 20, dtype=np.uint8)
        first = MemoryFrameSource("one.png", "image", [original], 1)
        second = MemoryFrameSource("two.png", "image", [np.full_like(original, 200)], 1)
        app.set_media(first)
        effect = ExposureEffect()
        effect.set_parameter("exposure", 2.0)
        app.set_pipeline(ProcessingPipeline([effect]))
        snapshot = app.snapshot()
        app.set_media(second)

        result = Application.process_snapshot(snapshot, 0)
        self.assertTrue(np.array_equal(result[0], original))
        self.assertTrue(np.array_equal(result[1], np.full_like(original, 40)))

    def test_memory_readers_return_copies(self) -> None:
        frame = np.full((2, 2, 4), 80, dtype=np.uint8)
        source = MemoryFrameSource("x.png", "image", [frame], 1)
        frame[0, 0, 0] = 0
        with source.open_reader() as reader:
            loaded = reader.get_frame(0)
        loaded[0, 0, 0] = 0
        with source.open_reader() as reader:
            unchanged = reader.get_frame(0)
        self.assertEqual(int(unchanged[0, 0, 0]), 80)

    def test_preset_round_trip_keeps_existing_wire_shape(self) -> None:
        preset = {"pipeline": [{"type": "Exposure", "name": "Exposure", "params": {"exposure": 1.5}}]}
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "in.json"
            output_path = Path(temp_dir) / "out.json"
            input_path.write_text(json.dumps(preset), encoding="utf-8")
            snapshot = Application.read_preset(str(input_path))
            Application.save_preset_snapshot(snapshot, str(output_path))
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), preset)

    def test_video_source_opens_independent_readers(self) -> None:
        class FakeCapture:
            def __init__(self, _path):
                self.released = False

            def isOpened(self):
                return True

            def get(self, prop):
                import cv2

                return 3 if prop == cv2.CAP_PROP_FRAME_COUNT else 24

            def set(self, *_args):
                return True

            def read(self):
                return True, np.zeros((2, 2, 3), dtype=np.uint8)

            def release(self):
                self.released = True

        captures = []

        def create_capture(path):
            capture = FakeCapture(path)
            captures.append(capture)
            return capture

        with patch("coldcamera.core.media_sources.cv2.VideoCapture", side_effect=create_capture):
            source = VideoFrameSource("clip.mp4")
            with source.open_reader() as first:
                first.get_frame(0)
            with source.open_reader() as second:
                second.get_frame(1)

        self.assertEqual(len(captures), 3)  # metadata handle, plus one per reader
        self.assertIsNot(captures[1], captures[2])
        self.assertTrue(captures[1].released)
        self.assertTrue(captures[2].released)

    def test_video_export_reads_with_a_private_reader_and_reports_progress(self) -> None:
        class FakeCapture:
            def __init__(self, _path):
                self.index = 0
                self.released = False

            def isOpened(self):
                return True

            def get(self, prop):
                import cv2

                return 2 if prop == cv2.CAP_PROP_FRAME_COUNT else 24

            def set(self, prop, value):
                self.index = int(value)
                return True

            def read(self):
                if self.index >= 2:
                    return False, None
                self.index += 1
                return True, np.full((2, 2, 3), 50, dtype=np.uint8)

            def release(self):
                self.released = True

        class FakeWriter:
            def __init__(self, *_args):
                self.frames = []

            def isOpened(self):
                return True

            def write(self, frame):
                self.frames.append(frame.copy())

            def release(self):
                return None

        captures = []
        writers = []

        def create_capture(path):
            capture = FakeCapture(path)
            captures.append(capture)
            return capture

        def create_writer(*args):
            writer = FakeWriter(*args)
            writers.append(writer)
            return writer

        progress = []
        snapshot = PipelineSnapshot.from_pipeline(ProcessingPipeline())
        with patch("coldcamera.core.media_sources.cv2.VideoCapture", side_effect=create_capture), patch(
            "coldcamera.core.media_service.cv2.VideoWriter", side_effect=create_writer
        ), patch("coldcamera.core.media_service.cv2.VideoWriter_fourcc", return_value=1):
            source = VideoFrameSource("source.mp4")
            MediaService.export_video(source, snapshot, "output.mp4", progress=lambda current, total: progress.append((current, total)))

        self.assertEqual(len(captures), 2)
        self.assertTrue(captures[0].released)
        self.assertTrue(captures[1].released)
        self.assertEqual(len(writers[0].frames), 2)
        self.assertEqual(progress[-1], (2, 2))

    def test_gif_export_reports_progress_and_honors_cancellation(self) -> None:
        source = MemoryFrameSource("animated.gif", "gif", [np.zeros((2, 2, 4), dtype=np.uint8)] * 2, 10)
        snapshot = PipelineSnapshot.from_pipeline(ProcessingPipeline())
        progress = []
        with tempfile.TemporaryDirectory() as temp_dir:
            output = str(Path(temp_dir) / "out.gif")
            MediaService.export_gif(source, snapshot, output, progress=lambda current, total: progress.append((current, total)))
            self.assertTrue(Path(output).is_file())
            self.assertEqual(progress[-1], (2, 2))

            cancelled_output = str(Path(temp_dir) / "cancelled.gif")
            token = CancellationToken()
            token.cancel()
            with self.assertRaises(OperationCancelled):
                MediaService.export_gif(source, snapshot, cancelled_output, cancellation=token)
            self.assertFalse(Path(cancelled_output).exists())


if __name__ == "__main__":
    unittest.main()
