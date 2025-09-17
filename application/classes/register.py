
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

