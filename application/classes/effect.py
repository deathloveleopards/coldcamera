
from typing import Optional, Dict, Any

from application.classes.parameter import EffectParam
from application.types import Processable
from application.exceptions import NotImplementedEffect, InvalidValue


class EffectBase:
    """
    Base class for all image processing effects.

    Each effect defines a set of parameters and provides
    a GLSL-based apply() method for rendering.

    :param name: Internal effect identifier (used in presets).
    :param label: Human-readable label for UI (localizable).
    :param hint: Optional description or tooltip (localizable).
    """

    def __init__(self, name: str, label: str, icon: Optional[str] = None, hint: Optional[str] = None):
        self.name = name
        self.label = label
        self.icon = icon
        self.hint = hint
        self.params = {}

    def apply(self, input_data: Processable) -> Processable:
        """
        Apply the effect to an image or sequence.
        Subclasses must override this method.

        :param input_data: Input image (PIL.Image or numpy.ndarray),
                           or sequence (ImageSequence).
        :return: Processed image or sequence in the same format.
        """
        raise NotImplementedEffect

    def to_dict(self) -> Dict[str, Any]:
        """Serialize effect with only parameter values."""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "label": self.label,
            "hint": self.hint,
            "params": {k: v.to_dict() for k, v in self.params.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EffectBase":
        """
        Reconstruct effect from dictionary.
        Assumes the effect subclass defines default params in __init__.
        """
        effect = cls(d["name"], d["label"], hint=d.get("hint"))
        params_data = d.get("params", {})

        for k, v in params_data.items():
            if k in effect.params:
                try:
                    effect.params[k] = EffectParam.from_dict(k, v, effect.params[k])
                except InvalidValue as e:
                    # TODO: Invalid Value error popup
                    raise InvalidValue(f"Invalid value for param '{k}' in effect '{effect.name}': {e}")
        return effect

    def set_param(self, name: str, value: Any) -> None:
        """Safely update a parameter value with validation."""
        if name not in self.params:
            raise KeyError(f"Unknown parameter: {name}")
        self.params[name].set_value(value)

    def get_param(self, name: str) -> Any:
        """Get current value of a parameter."""
        if name not in self.params:
            raise KeyError(f"Unknown parameter: {name}")
        return self.params[name].value

    def __repr__(self) -> str:
        params_str = ", ".join(f"{k}={v.value!r}" for k, v in self.params.items())
        return f"<{self.__class__.__name__} name={self.name!r}, params={{ {params_str} }}>"