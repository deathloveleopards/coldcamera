"""Backward-compatible path-backed video source facade."""

from __future__ import annotations

import numpy as np

from coldcamera.core.media_sources import VideoFrameSource


class VideoFrameProvider(VideoFrameSource):
    """Video source that opens a separate reader for each frame request."""

    @property
    def frame_count(self) -> int:
        return self.info.frame_count

    @property
    def fps(self) -> int:
        return self.info.fps

    def get_frame(self, index: int) -> np.ndarray | None:
        with self.open_reader() as reader:
            return reader.get_frame(index)

    def release(self) -> None:
        """Kept for callers of the previous persistent-capture API."""

        return None
