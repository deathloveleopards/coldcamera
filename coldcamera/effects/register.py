"""Processing effect names and stable class lookup for preset loading."""

from __future__ import annotations

from typing import Optional, Type

from coldcamera.classes.effect import EffectBase
from coldcamera.effects.includes.blur import BlurEffect
from coldcamera.effects.includes.ccd_smear import CCDSmearEffect
from coldcamera.effects.includes.chromatic_abberation import ChromaticAberrationEffect
from coldcamera.effects.includes.contrast_brightness import ContrastBrightnessEffect
from coldcamera.effects.includes.exposure import ExposureEffect
from coldcamera.effects.includes.film_grain import FilmGrainEffect
from coldcamera.effects.includes.ghosting import GhostingEffect
from coldcamera.effects.includes.glow import GlowEffect
from coldcamera.effects.includes.hue import HueEffect
from coldcamera.effects.includes.jpeg_damage import JpegDamageEffect
from coldcamera.effects.includes.noise import NoiseEffect
from coldcamera.effects.includes.rescale import RescaleEffect
from coldcamera.effects.includes.s_chorus import ChorusEffect
from coldcamera.effects.includes.s_delay import DelayEffect
from coldcamera.effects.includes.s_distortion import DistortionEffect
from coldcamera.effects.includes.s_highpass import HighPassEffect
from coldcamera.effects.includes.s_limiter import LimiterEffect
from coldcamera.effects.includes.s_lowpass import LowPassEffect
from coldcamera.effects.includes.s_phaser import PhaserEffect
from coldcamera.effects.includes.s_reverb import ReverbEffect
from coldcamera.effects.includes.sharpen import SharpenEffect
from coldcamera.effects.includes.vibrance import VibranceEffect
from coldcamera.effects.includes.warmth import WarmthEffect

EFFECT_CLASSES: dict[str, Type[EffectBase]] = {
    "Exposure": ExposureEffect,
    "Contrast/Brightness": ContrastBrightnessEffect,
    "HUE": HueEffect,
    "Warmth": WarmthEffect,
    "Vibrance": VibranceEffect,
    "Rescale": RescaleEffect,
    "Sharpen": SharpenEffect,
    "Chromatic Aberration": ChromaticAberrationEffect,
    "Ghosting": GhostingEffect,
    "CCD Smear": CCDSmearEffect,
    "JPEG Damage": JpegDamageEffect,
    "Glow": GlowEffect,
    "Blur": BlurEffect,
    "Film Grain": FilmGrainEffect,
    "Noise": NoiseEffect,
    "Chorus": ChorusEffect,
    "Delay": DelayEffect,
    "Distortion": DistortionEffect,
    "High Pass": HighPassEffect,
    "Limiter": LimiterEffect,
    "Low Pass": LowPassEffect,
    "Phaser": PhaserEffect,
    "Reverb": ReverbEffect,
}

_EFFECT_CLASS_TO_NAME = {effect_class: name for name, effect_class in EFFECT_CLASSES.items()}


def get_by_name(name: str) -> Optional[Type[EffectBase]]:
    """Resolve the stable preset name for an effect class."""

    return EFFECT_CLASSES.get(name)


def get_name_for_class(effect_class: Type[EffectBase]) -> Optional[str]:
    """Return the stable preset name for an effect class."""

    return _EFFECT_CLASS_TO_NAME.get(effect_class)
