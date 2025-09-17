
from typing import Type, Optional

from application.classes.effect import EffectBase
from application.effects.exposure import ExposureEffect
from application.effects.contrast_brightness import ContrastBrightnessEffect
from application.effects.hue import HueEffect
from application.effects.warmth import WarmthEffect
from application.effects.vibrance import VibranceEffect
from application.effects.sharpen import SharpenEffect
from application.effects.blur import BlurEffect
from application.effects.rescale import RescaleEffect
from application.effects.noise import NoiseEffect
from application.effects.glow import GlowEffect
from application.effects.film_grain import FilmGrainEffect
from application.effects.chromatic_abberation import ChromaticAberrationEffect
from application.effects.jpeg_damage import JpegDamageEffect
from application.effects.ghosting import GhostingEffect
from application.effects.ccd_smear import CCDSmearEffect


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