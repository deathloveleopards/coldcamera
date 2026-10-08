"""Presentation descriptors consumed by GUI adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from coldcamera.classes.effect import EffectBase
from coldcamera.effects.register import EFFECT_CLASSES
from coldcamera.enums import BlendModeType, ChromaticAberrationType, NoiseType, RescaleResolution


@dataclass(frozen=True)
class EffectDescriptor:
    category: str
    name: str
    effect_class: Type[EffectBase]
    editor_elements: tuple[dict[str, Any], ...]


def _slider(name: str, label: str, minimum: float, maximum: float, step: float = 1) -> dict[str, Any]:
    return {"type": "param_slider", "name": name, "label": label, "min": minimum, "max": maximum, "step": step}


def _spinbox(name: str, label: str, minimum: int, maximum: int, step: int = 1) -> dict[str, Any]:
    return {"type": "param_spinbox", "name": name, "label": label, "min": minimum, "max": maximum, "step": step}


def _checkbox(name: str, label: str) -> dict[str, Any]:
    return {"type": "param_checkbox", "name": name, "label": label}


def _dropdown(name: str, label: str, enum_type: type) -> dict[str, Any]:
    return {
        "type": "param_dropdown",
        "name": name,
        "label": label,
        "options": [item.label for item in enum_type],
        "values": [item.code for item in enum_type],
    }


_EDITOR_LAYOUTS: dict[str, tuple[dict[str, Any], ...]] = {
    "Exposure": (_slider("exposure", "Exposure", 0.5, 2.0, 0.05),),
    "Contrast/Brightness": (_slider("contrast", "Contrast", 0.5, 3.0, 0.1), _slider("brightness", "Brightness", -100, 100)),
    "HUE": (_slider("hue_shift", "Shift", -180.0, 180.0),),
    "Warmth": (_slider("warmth", "Warmth", -50, 50),),
    "Vibrance": (_slider("vibrance", "Vibrance", -100, 100), _slider("saturation", "Saturation", -100, 100)),
    "Rescale": (_dropdown("resolution", "Resolution", RescaleResolution), _checkbox("adaptive", "Adaptive orientation")),
    "Sharpen": (_slider("amount", "Amount", 0.0, 3.0, 0.1), _slider("radius", "Radius", 1, 10)),
    "Chromatic Aberration": (
        _slider("shift", "Shift", -20, 20),
        _slider("rotation", "Rotation", 0, 360),
        _dropdown("ab_type", "Channel combo", ChromaticAberrationType),
    ),
    "Ghosting": (
        _slider("strength", "Ghost strength", 0.0, 1.0, 0.01),
        _spinbox("offset_x", "Offset X", -20, 20),
        _spinbox("offset_y", "Offset Y", -20, 20),
        _spinbox("blur_radius", "Blur radius", 0, 21, 2),
    ),
    "CCD Smear": (
        _slider("smear_threshold", "Threshold", 0, 255),
        _slider("smear_strength", "Smear Strength", 0.0, 1.0, 0.01),
        _slider("smear_h_blur", "Horizontal Blur", 0, 21, 2),
        _slider("smear_color_r", "Smear Color R", 0, 255),
        _slider("smear_color_g", "Smear Color G", 0, 255),
        _slider("smear_color_b", "Smear Color B", 0, 255),
        _slider("smear_falloff", "Smear Falloff", 0.0, 1.0, 0.01),
        _checkbox("use_mask", "Use Mask"),
    ),
    "JPEG Damage": (_spinbox("quality", "Quality", 1, 100),),
    "Glow": (
        _slider("radius", "Glow radius", 0, 100),
        _slider("intensity", "Glow intensity", 0, 5, 0.1),
        _slider("light_threshold", "Light threshold", 0, 1, 0.01),
        _slider("opacity", "Opacity", 0, 1, 0.05),
        _dropdown("blend_mode", "Blend mode", BlendModeType),
    ),
    "Blur": (
        _slider("amount", "Blur amount", 0, 100),
        _slider("angle", "Blur angle", -180, 180),
        _slider("opacity", "Opacity", 0, 1, 0.05),
        _dropdown("blend_mode", "Blend mode", BlendModeType),
    ),
    "Film Grain": (
        _slider("grain_strength", "Grain Strength", 0, 100),
        _slider("grain_size", "Grain Size", 0.5, 5.0, 0.1),
        _checkbox("color_grain", "Color Grain"),
    ),
    "Noise": (
        _slider("strength", "Noise strength", 0, 100),
        _slider("opacity", "Opacity", 0, 1, 0.05),
        _dropdown("type", "Noise type", NoiseType),
        _dropdown("blend_mode", "Blend mode", BlendModeType),
    ),
    "Chorus": (_slider("rate", "Rate", 0.5, 4.0, 0.1), _slider("depth", "Depth", 0.0, 1.0, 0.1)),
    "Delay": (
        _slider("delay_seconds", "Delay (s)", 0.0, 30.0, 0.1),
        _slider("feedback", "Feedback", 0.0, 1.0, 0.05),
        _slider("mix", "Mix", 0.0, 1.0, 0.05),
    ),
    "Distortion": (_slider("drive", "Drive", -40.0, 40.0, 0.5),),
    "High Pass": (_slider("cutoff_frequency_hz", "Cutoff Frequency", 10.0, 20000.0),),
    "Limiter": (_slider("threshold", "Threshold", -40.0, 40.0, 0.5),),
    "Low Pass": (_slider("cutoff_frequency_hz", "Cutoff Frequency", 10.0, 20000.0),),
    "Phaser": (_slider("rate", "Rate", 0.0, 10.0, 0.1), _slider("depth", "Depth", 0.0, 1.0, 0.1)),
    "Reverb": (_slider("room_size", "Room Size", 0.0, 1.0, 0.5),),
}


_CATEGORY_EFFECTS = {
    "Color": ("Exposure", "Contrast/Brightness", "HUE", "Warmth", "Vibrance"),
    "Basic": ("Rescale", "Sharpen"),
    "Distort": ("Chromatic Aberration", "Ghosting", "CCD Smear", "JPEG Damage"),
    "Artistic": ("Glow", "Blur", "Film Grain", "Noise"),
    "Sonarify": ("Chorus", "Delay", "Distortion", "High Pass", "Limiter", "Low Pass", "Phaser", "Reverb"),
}

EFFECT_DESCRIPTORS: dict[str, dict[str, EffectDescriptor]] = {
    category: {
        name: EffectDescriptor(category, name, EFFECT_CLASSES[name], _EDITOR_LAYOUTS.get(name, ()))
        for name in names
    }
    for category, names in _CATEGORY_EFFECTS.items()
}

_BY_CLASS = {descriptor.effect_class: descriptor for group in EFFECT_DESCRIPTORS.values() for descriptor in group.values()}


def get_effect_descriptor(effect_class: Type[EffectBase]) -> EffectDescriptor:
    try:
        return _BY_CLASS[effect_class]
    except KeyError as exc:
        raise ValueError(f"No editor descriptor registered for {effect_class.__name__}") from exc
