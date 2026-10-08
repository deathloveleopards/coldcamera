"""Media source and reader abstractions used by the backend."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, Protocol

import cv2
import numpy as np

from coldcamera.exceptions import VideoOpenError

MediaKind = Literal["image", "gif", "video"]


@dataclass(frozen=True)
class MediaInfo:
    """Immutable metadata about an opened media source."""

    path: str
    kind: MediaKind
    frame_count: int
    fps: int


class FrameReader(Protocol):
    """A task-scoped reader. Callers must close it when finished."""

    def get_frame(self, index: int) -> np.ndarray | None: ...

    def iter_frames(self) -> Iterator[tuple[int, np.ndarray]]: ...

    def close(self) -> None: ...


class FrameSource(Protocol):
    """Metadata plus a factory for independent frame readers."""

    @property
    def info(self) -> MediaInfo: ...

    def open_reader(self) -> AbstractContextManager[FrameReader]: ...


class _MemoryFrameReader:
    def __init__(self, frames: tuple[np.ndarray, ...]):
        self._frames = frames

    def get_frame(self, index: int) -> np.ndarray | None:
        if index < 0 or index >= len(self._frames):
            return None
        return self._frames[index].copy()

    def iter_frames(self) -> Iterator[tuple[int, np.ndarray]]:
        for index, frame in enumerate(self._frames):
            yield index, frame.copy()

    def close(self) -> None:
        return None

    def __enter__(self) -> "_MemoryFrameReader":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


class MemoryFrameSource:
    """Eager in-memory source for still images and currently eager GIFs."""

    def __init__(self, path: str, kind: Literal["image", "gif"], frames: list[np.ndarray] | tuple[np.ndarray, ...], fps: int):
        if not frames:
            raise ValueError("A media source must contain at least one frame")
        # Own the buffers so snapshots stay stable if the caller later reuses its arrays.
        self._frames = tuple(frame.copy() for frame in frames)
        self._info = MediaInfo(path=path, kind=kind, frame_count=len(self._frames), fps=max(1, int(fps)))

    @property
    def info(self) -> MediaInfo:
        return self._info

    def open_reader(self) -> _MemoryFrameReader:
        return _MemoryFrameReader(self._frames)


class VideoFrameReader:
    """An independent OpenCV capture handle for one backend operation."""

    def __init__(self, path: str, frame_count: int):
        self._frame_count = frame_count
        self._capture = cv2.VideoCapture(path)
        if not self._capture.isOpened():
            self._capture.release()
            raise VideoOpenError(path=path)

    def get_frame(self, index: int) -> np.ndarray | None:
        if index < 0 or index >= self._frame_count:
            return None
        # Some backends return False even though seeking works; always test read().
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self._capture.read()
        if not ret:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    def iter_frames(self) -> Iterator[tuple[int, np.ndarray]]:
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        for index in range(self._frame_count):
            ret, frame = self._capture.read()
            if not ret:
                break
            yield index, cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    def close(self) -> None:
        self._capture.release()

    def __enter__(self) -> "VideoFrameReader":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


class VideoFrameSource:
    """Path-backed video source; each operation receives a private reader."""

    def __init__(self, path: str):
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            raise VideoOpenError(path=path)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_value = capture.get(cv2.CAP_PROP_FPS) or 25
        capture.release()
        self._path = str(Path(path))
        self._info = MediaInfo(path=self._path, kind="video", frame_count=frame_count, fps=max(1, int(fps_value)))

    @property
    def info(self) -> MediaInfo:
        return self._info

    @property
    def frame_count(self) -> int:
        return self._info.frame_count

    @property
    def fps(self) -> int:
        return self._info.fps

    def open_reader(self) -> VideoFrameReader:
        return VideoFrameReader(self._path, self._info.frame_count)

    def get_frame(self, index: int) -> np.ndarray | None:
        with self.open_reader() as reader:
            return reader.get_frame(index)

    def release(self) -> None:
        """Retained as a compatibility no-op; readers are operation-scoped."""

        return None
