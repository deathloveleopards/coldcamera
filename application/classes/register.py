
from typing import Dict, Type

from application.classes.effect import EffectBase


EFFECT_REGISTRY: Dict[str, Type[EffectBase]] = {}