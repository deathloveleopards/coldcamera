"""Qt-independent media loading, frame processing, and exporting."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import cv2
import numpy as np
from PIL import Image, ImageSequence

from coldcamera.classes.pipeline import ProcessingPipeline
from coldcamera.core.image_processor import ImageProcessor
from coldcamera.core.media_sources import FrameSource, MediaKind, MemoryFrameSource, VideoFrameSource
from coldcamera.core.operations import CancellationToken, ProgressCallback, report_progress
from coldcamera.core.pipeline_snapshot import PipelineSnapshot

PipelineInput = ProcessingPipeline | PipelineSnapshot


class MediaService:
    """Synchronous media operations with no Qt dependencies."""

    @staticmethod
    def load_image(path: str) -> np.ndarray:
        with Image.open(path) as image:
            return np.array(image.convert("RGBA"), dtype=np.uint8)

    @classmethod
    def load_image_source(cls, path: str) -> MemoryFrameSource:
        return MemoryFrameSource(path, "image", [cls.load_image(path)], 1)

    @staticmethod
    def load_gif_frames(path: str) -> tuple[list[np.ndarray], int]:
        with Image.open(path) as image:
            frames = [np.array(frame.convert("RGBA"), dtype=np.uint8) for frame in ImageSequence.Iterator(image)]
            duration = image.info.get("duration", 100)
        fps = max(1, int(1000 / duration)) if duration else 10
        return frames, fps

    @classmethod
    def load_gif_source(cls, path: str) -> MemoryFrameSource:
        frames, fps = cls.load_gif_frames(path)
        return MemoryFrameSource(path, "gif", frames, fps)

    @staticmethod
    def load_video(path: str) -> VideoFrameSource:
        return VideoFrameSource(path)

    @classmethod
    def load_source(cls, path: str, kind: MediaKind | None = None) -> FrameSource:
        resolved_kind = kind or cls.kind_from_path(path)
        if resolved_kind == "image":
            return cls.load_image_source(path)
        if resolved_kind == "gif":
            return cls.load_gif_source(path)
        if resolved_kind == "video":
            return cls.load_video(path)
        raise ValueError(f"Unsupported media type: {resolved_kind}")

    @staticmethod
    def kind_from_path(path: str) -> MediaKind:
        suffix = Path(path).suffix.lower()
        if suffix == ".gif":
            return "gif"
        if suffix in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
            return "video"
        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}:
            return "image"
        raise ValueError(f"Unsupported media file: {path}")

    @staticmethod
    def _pipeline_for_operation(pipeline: PipelineInput) -> ProcessingPipeline:
        if isinstance(pipeline, PipelineSnapshot):
            return pipeline.build_pipeline()
        return PipelineSnapshot.from_pipeline(pipeline).build_pipeline()

    @classmethod
    def process_source_frame(
        cls,
        source: FrameSource,
        frame_index: int,
        pipeline: PipelineInput,
        cancellation: CancellationToken | None = None,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        with source.open_reader() as reader:
            original = reader.get_frame(frame_index)
        if original is None:
            return None
        runtime_pipeline = cls._pipeline_for_operation(pipeline)
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        processed = ImageProcessor.process_frame(runtime_pipeline, original.copy())
        if processed is None:
            return None
        return original, ImageProcessor.ensure_rgba(processed)

    @staticmethod
    def export_image(frame: np.ndarray, path: str) -> None:
        frame = ImageProcessor.ensure_uint8(frame)
        if frame.ndim == 3 and frame.shape[2] == 4:
            image = Image.fromarray(frame).convert("RGB")
        elif frame.ndim == 3 and frame.shape[2] == 3:
            image = Image.fromarray(frame)
        else:
            raise ValueError(f"Unsupported array shape for export: {frame.shape}")
        image.save(path)

    @classmethod
    def export_processed_image(
        cls,
        source: FrameSource,
        frame_index: int,
        pipeline: PipelineInput,
        path: str,
        cancellation: CancellationToken | None = None,
    ) -> None:
        result = cls.process_source_frame(source, frame_index, pipeline, cancellation)
        if result is None:
            raise ValueError("No image frame is available to export")
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        cls.export_image(result[1], path)

    @classmethod
    def export_gif(
        cls,
        source: FrameSource,
        pipeline: PipelineInput,
        path: str,
        *,
        fps: int | None = None,
        progress: ProgressCallback | None = None,
        cancellation: CancellationToken | None = None,
    ) -> None:
        runtime_pipeline = cls._pipeline_for_operation(pipeline)
        processed_frames: list[Image.Image] = []
        total = source.info.frame_count

        with source.open_reader() as reader:
            for current, (_index, frame) in enumerate(reader.iter_frames(), start=1):
                if cancellation is not None:
                    cancellation.raise_if_cancelled()
                processed = ImageProcessor.process_frame(runtime_pipeline, frame)
                if processed is not None:
                    if processed.ndim != 3 or processed.shape[2] not in (3, 4):
                        raise ValueError(f"Unsupported channel count: {processed.shape[-1] if processed.ndim else 0}")
                    processed_frames.append(Image.fromarray(processed))
                report_progress(progress, current, total)

        if not processed_frames:
            raise ValueError("No frames were processed")
        output_fps = max(1, fps or source.info.fps)
        processed_frames[0].save(
            path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=int(1000 / output_fps),
            loop=0,
            optimize=False,
        )

    @classmethod
    def export_video(
        cls,
        source: FrameSource,
        pipeline: PipelineInput,
        path: str,
        *,
        progress: ProgressCallback | None = None,
        cancellation: CancellationToken | None = None,
    ) -> None:
        runtime_pipeline = cls._pipeline_for_operation(pipeline)
        total = source.info.frame_count
        writer = None
        processed_count = 0

        with source.open_reader() as reader:
            frame_iterator = reader.iter_frames()
            try:
                for current, (_index, rgba_frame) in enumerate(frame_iterator, start=1):
                    if cancellation is not None:
                        cancellation.raise_if_cancelled()
                    if writer is None:
                        height, width = rgba_frame.shape[:2]
                        fourcc = cv2.VideoWriter_fourcc(*("XVID" if path.lower().endswith(".avi") else "mp4v"))
                        writer = cv2.VideoWriter(path, fourcc, source.info.fps, (width, height))
                        if not writer.isOpened():
                            raise OSError(f"Cannot open video output: {path}")

                    processed = ImageProcessor.process_frame(runtime_pipeline, rgba_frame)
                    if processed is None:
                        continue
                    if processed.shape[2] == 4:
                        processed_rgb = cv2.cvtColor(processed, cv2.COLOR_RGBA2RGB)
                    elif processed.shape[2] == 3:
                        processed_rgb = processed
                    else:
                        raise ValueError(f"Unsupported channel count: {processed.shape[2]}")
                    writer.write(cv2.cvtColor(processed_rgb, cv2.COLOR_RGB2BGR))
                    processed_count += 1
                    report_progress(progress, current, total)
            finally:
                if writer is not None:
                    writer.release()

        if processed_count == 0:
            raise ValueError("No video frames were processed")

    @staticmethod
    def iter_frames(source: FrameSource) -> Iterator[tuple[int, np.ndarray]]:
        with source.open_reader() as reader:
            yield from reader.iter_frames()
