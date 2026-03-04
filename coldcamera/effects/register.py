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

EFFECT_REGISTRY = {
    "Color": {
        "Exposure": ExposureEffect,
        "Contrast/Brightness": ContrastBrightnessEffect,
        "HUE": HueEffect,
        "Warmth": WarmthEffect,
        "Vibrance": VibranceEffect,
    },
    "Basic": {
        "Rescale": RescaleEffect,
        "Sharpen": SharpenEffect,
    },
    "Distort": {
        "Chromatic Aberration": ChromaticAberrationEffect,
        "Ghosting": GhostingEffect,
        "CCD Smear": CCDSmearEffect,
        "JPEG Damage": JpegDamageEffect,
    },
    "Artistic": {
        "Glow": GlowEffect,
        "Blur": BlurEffect,
        "Film Grain": FilmGrainEffect,
        "Noise": NoiseEffect,
    },
    "Sonarify": {
        "Chorus": ChorusEffect,
        "Delay": DelayEffect,
        "Distortion": DistortionEffect,
        "High Pass": HighPassEffect,
        "Limiter": LimiterEffect,
        "Low Pass": LowPassEffect,
        "Phaser": PhaserEffect,
        "Reverb": ReverbEffect,
    },
}

# Build reverse maps (class -> display name, name -> class)
_EFFECT_NAME_TO_CLASS: dict[str, Type[EffectBase]] = {}
_EFFECT_CLASS_TO_NAME: dict[Type[EffectBase], str] = {}

for category, effects in EFFECT_REGISTRY.items():
    for display_name, cls in effects.items():
        _EFFECT_NAME_TO_CLASS[display_name] = cls
        _EFFECT_CLASS_TO_NAME[cls] = display_name


def get_by_name(name: str) -> Optional[Type[EffectBase]]:
    """
    Resolve an effect class from a display name.

    :param name: The human-readable effect name as in EFFECT_REGISTRY (e.g. "Exposure").
    :return: Effect class, or None if not found.
    """

    return _EFFECT_NAME_TO_CLASS.get(name)


def get_name_for_class(cls: Type[EffectBase]) -> Optional[str]:
    """
    Resolve the display name for a given effect class.

    :param cls: Effect class.
    :return: Display name string if found, else None.
    """

    return _EFFECT_CLASS_TO_NAME.get(cls)
