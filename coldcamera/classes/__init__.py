"""Core processing classes, lazily exported to avoid import cycles."""

from importlib import import_module

__all__ = ["EffectBase", "EffectParam", "EffectParamManager", "ProcessingPipeline", "ShaderProcessorBase", "VideoFrameProvider"]

_EXPORTS = {
    "EffectBase": ("coldcamera.classes.effect", "EffectBase"),
    "EffectParam": ("coldcamera.classes.parameter", "EffectParam"),
    "EffectParamManager": ("coldcamera.classes.parameters_manager", "EffectParamManager"),
    "ProcessingPipeline": ("coldcamera.classes.pipeline", "ProcessingPipeline"),
    "ShaderProcessorBase": ("coldcamera.classes.shader_processor", "ShaderProcessorBase"),
    "VideoFrameProvider": ("coldcamera.classes.video_provider", "VideoFrameProvider"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute_name = _EXPORTS[name]
    return getattr(import_module(module_name), attribute_name)
