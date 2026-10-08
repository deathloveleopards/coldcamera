"""Qt-independent backend primitives, lazily exported."""

from importlib import import_module

__all__ = [
    "CancellationToken",
    "FrameReader",
    "FrameSource",
    "ImageProcessor",
    "MediaInfo",
    "MediaService",
    "MemoryFrameSource",
    "OperationCancelled",
    "PipelineSnapshot",
    "VideoFrameSource",
]

_EXPORTS = {
    "CancellationToken": ("coldcamera.core.operations", "CancellationToken"),
    "FrameReader": ("coldcamera.core.media_sources", "FrameReader"),
    "FrameSource": ("coldcamera.core.media_sources", "FrameSource"),
    "ImageProcessor": ("coldcamera.core.image_processor", "ImageProcessor"),
    "MediaInfo": ("coldcamera.core.media_sources", "MediaInfo"),
    "MediaService": ("coldcamera.core.media_service", "MediaService"),
    "MemoryFrameSource": ("coldcamera.core.media_sources", "MemoryFrameSource"),
    "OperationCancelled": ("coldcamera.core.operations", "OperationCancelled"),
    "PipelineSnapshot": ("coldcamera.core.pipeline_snapshot", "PipelineSnapshot"),
    "VideoFrameSource": ("coldcamera.core.media_sources", "VideoFrameSource"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    return getattr(import_module(module_name), attribute_name)
