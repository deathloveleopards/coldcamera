"""Qt-independent application API and GUI entry point."""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from typing import Optional

import numpy as np

from coldcamera.classes.pipeline import ProcessingPipeline
from coldcamera.config import APPLICATION_VERSION
from coldcamera.core.media_service import MediaService
from coldcamera.core.media_sources import FrameSource, MediaInfo, MediaKind
from coldcamera.core.operations import CancellationToken, ProgressCallback
from coldcamera.core.pipeline_snapshot import PipelineSnapshot
from coldcamera.logger import initialize_logger, logger


@dataclass(frozen=True)
class ApplicationSnapshot:
    """Detached state required by one asynchronous operation."""

    media: FrameSource | None
    pipeline: PipelineSnapshot

    @property
    def media_info(self) -> MediaInfo | None:
        return self.media.info if self.media is not None else None


class Application:
    """Synchronous, Qt-free use-case API shared by all frontends."""

    def __init__(self) -> None:
        initialize_logger()
        logger.info("Start application")
        logger.debug(f"Application version: {APPLICATION_VERSION}")
        logger.debug(f"Platform: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
        self._media: FrameSource | None = None
        self._pipeline = PipelineSnapshot.from_pipeline(ProcessingPipeline())
        self._current_frame_index = 0
        logger.success("Application is fully initialized!")

    @property
    def has_media(self) -> bool:
        return self._media is not None

    @property
    def media_info(self) -> MediaInfo | None:
        return self._media.info if self._media is not None else None

    @property
    def current_frame_index(self) -> int:
        return self._current_frame_index

    @current_frame_index.setter
    def current_frame_index(self, value: int) -> None:
        self._current_frame_index = value

    def snapshot(self) -> ApplicationSnapshot:
        """Capture media and pipeline references for an isolated task."""

        return ApplicationSnapshot(media=self._media, pipeline=self._pipeline)

    def set_pipeline(self, pipeline: ProcessingPipeline | PipelineSnapshot) -> None:
        """Replace the active pipeline using a detached serializable snapshot."""

        self._pipeline = pipeline if isinstance(pipeline, PipelineSnapshot) else PipelineSnapshot.from_pipeline(pipeline)

    def set_media(self, media: FrameSource) -> MediaInfo:
        """Commit successfully loaded media while preserving operation snapshots."""

        self._media = media
        self._current_frame_index = 0
        return media.info

    @staticmethod
    def prepare_media(path: str, kind: MediaKind | None = None) -> FrameSource:
        """Load and validate media without mutating application state."""

        return MediaService.load_source(path, kind)

    def open_media(self, path: str, kind: MediaKind | None = None) -> MediaInfo:
        """Synchronously load and commit media; suitable for a CLI caller."""

        media = self.prepare_media(path, kind)
        info = self.set_media(media)
        logger.info(f"Media opened: {path} ({info.frame_count} frames, {info.fps} fps)")
        return info

    def open_image(self, path: str) -> np.ndarray:
        media = self.prepare_media(path, "image")
        with media.open_reader() as reader:
            frame = reader.get_frame(0)
        if frame is None:
            raise ValueError(f"Could not read image: {path}")
        self.set_media(media)
        logger.info(f"Image opened: {path}")
        return frame

    def open_gif(self, path: str) -> tuple[list[np.ndarray], int]:
        media = self.prepare_media(path, "gif")
        with media.open_reader() as reader:
            frames = list(frame for _index, frame in reader.iter_frames())
        self.set_media(media)
        logger.info(f"GIF opened: {path} ({len(frames)} frames, {media.info.fps} fps)")
        return frames, media.info.fps

    def open_video(self, path: str) -> tuple[int, int]:
        media = self.prepare_media(path, "video")
        self.set_media(media)
        logger.info(f"Video opened: {path} ({media.info.frame_count} frames, {media.info.fps} fps)")
        return media.info.frame_count, media.info.fps

    def get_original_frame(self, frame_index: Optional[int] = None) -> Optional[np.ndarray]:
        snapshot = self.snapshot()
        index = self._current_frame_index if frame_index is None else frame_index
        if snapshot.media is None:
            return None
        with snapshot.media.open_reader() as reader:
            return reader.get_frame(index)

    def process_current(self, frame_index: Optional[int] = None) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if frame_index is not None:
            self._current_frame_index = frame_index
        return self.process_snapshot(self.snapshot(), self._current_frame_index)

    @staticmethod
    def process_snapshot(
        snapshot: ApplicationSnapshot,
        frame_index: int = 0,
        cancellation: CancellationToken | None = None,
    ) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if snapshot.media is None:
            return None, None
        result = MediaService.process_source_frame(snapshot.media, frame_index, snapshot.pipeline, cancellation)
        return result if result is not None else (None, None)

    @staticmethod
    def export_image_from_snapshot(
        snapshot: ApplicationSnapshot,
        path: str,
        frame_index: int = 0,
        cancellation: CancellationToken | None = None,
    ) -> None:
        if snapshot.media is None or snapshot.media.info.kind != "image":
            raise ValueError("No image loaded to export")
        MediaService.export_processed_image(snapshot.media, frame_index, snapshot.pipeline, path, cancellation)
        logger.info(f"Image exported: {path}")

    @staticmethod
    def export_gif_from_snapshot(
        snapshot: ApplicationSnapshot,
        path: str,
        *,
        progress: ProgressCallback | None = None,
        cancellation: CancellationToken | None = None,
    ) -> None:
        if snapshot.media is None or snapshot.media.info.kind != "gif":
            raise ValueError("No GIF loaded to export")
        MediaService.export_gif(snapshot.media, snapshot.pipeline, path, progress=progress, cancellation=cancellation)
        logger.info(f"GIF exported: {path}")

    @staticmethod
    def export_video_from_snapshot(
        snapshot: ApplicationSnapshot,
        path: str,
        *,
        progress: ProgressCallback | None = None,
        cancellation: CancellationToken | None = None,
    ) -> None:
        if snapshot.media is None or snapshot.media.info.kind != "video":
            raise ValueError("No video loaded to export")
        MediaService.export_video(snapshot.media, snapshot.pipeline, path, progress=progress, cancellation=cancellation)
        logger.info(f"Video exported: {path}")

    def save_preset(self, path: str) -> None:
        self.save_preset_snapshot(self._pipeline, path)

    @staticmethod
    def save_preset_snapshot(pipeline: PipelineSnapshot, path: str) -> None:
        # Keep the established preset wire format; enabled flags remain a UI setting as before.
        pipeline.build_pipeline().save_preset(path)
        logger.info(f"Preset saved: {path}")

    @staticmethod
    def read_preset(path: str) -> PipelineSnapshot:
        with open(path, "r", encoding="utf-8") as preset_file:
            data = json.load(preset_file)
        # Validate the preset in the worker before delivering it to the UI.
        ProcessingPipeline.from_dictionary(data)
        return PipelineSnapshot.from_dictionary(data)

    def load_preset(self, path: str) -> ProcessingPipeline:
        snapshot = self.read_preset(path)
        self._pipeline = snapshot
        logger.info(f"Preset loaded: {path}")
        return snapshot.build_pipeline()


def run_gui() -> None:
    """Launch the PySide6 interface (imports Qt only at the UI entry point)."""

    import sys

    import qdarktheme
    from PySide6.QtWidgets import QApplication

    from coldcamera.window import MainWindow

    app = Application()
    qt_app = QApplication(sys.argv)
    qdarktheme.setup_theme(custom_colors={"background": "#191a1c", "primary": "#ffffff", "border": "#2a2b2b"})
    window = MainWindow(app)
    window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    run_gui()
