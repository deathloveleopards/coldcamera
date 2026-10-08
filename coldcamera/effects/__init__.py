"""Effect implementations, lazily exported for lightweight imports."""

from importlib import import_module

__all__ = [
    "BlurEffect",
    "CCDSmearEffect",
    "ChromaticAberrationEffect",
    "ContrastBrightnessEffect",
    "ExposureEffect",
    "FilmGrainEffect",
    "GhostingEffect",
    "GlowEffect",
    "HueEffect",
    "JpegDamageEffect",
    "NoiseEffect",
    "RescaleEffect",
    "SharpenEffect",
    "VibranceEffect",
    "WarmthEffect",
]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(name)
    module_name = "coldcamera.effects.includes." + {
        "CCDSmearEffect": "ccd_smear",
        "ChromaticAberrationEffect": "chromatic_abberation",
        "ContrastBrightnessEffect": "contrast_brightness",
        "FilmGrainEffect": "film_grain",
        "JpegDamageEffect": "jpeg_damage",
    }.get(name, name.removesuffix("Effect").lower())
    return getattr(import_module(module_name), name)
