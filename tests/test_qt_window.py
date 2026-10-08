from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PIL import Image
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from coldcamera.application import Application
from coldcamera.window import MainWindow


class QtWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_image_open_and_preview_complete_through_background_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "sample.png"
            Image.fromarray(np.full((3, 4, 4), 100, dtype=np.uint8)).save(image_path)
            with patch("coldcamera.application.initialize_logger"):
                app = Application()
            window = MainWindow(app)
            window.pipeline_widget.add_effect("Blur")
            self.assertIsNone(window.pipeline_widget.pipeline.effects[0].processor)
            loop = QEventLoop()
            timer = QTimer()
            timer.setInterval(20)
            elapsed = 0

            def check_complete() -> None:
                nonlocal elapsed
                elapsed += 20
                if window.viewport.processed_qimage is not None or elapsed >= 10_000:
                    loop.quit()

            timer.timeout.connect(check_complete)
            timer.start()
            window._start_load(str(image_path), "image")
            loop.exec()
            timer.stop()

            self.assertTrue(app.has_media)
            self.assertEqual(app.media_info.path, str(image_path))
            self.assertIsNotNone(window.viewport.processed_qimage)
            self.assertEqual(window.viewport.processed_qimage.width(), 4)
            window.close()


if __name__ == "__main__":
    unittest.main()
