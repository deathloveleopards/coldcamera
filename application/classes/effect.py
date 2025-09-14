
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from application.classes.parameter import EffectParam
from application.classes.parameters_manager import EffectParamManager
from application.exceptions import NotImplementedEffect
from application.types import Processable


class EffectBase(ABC):
    """
    Abstract base class for all image processing effects.

    Each effect defines a set of parameters (via EffectParamManager),
    provides an `apply()` method for rendering, and a declarative
    `layout` description for building UI components.

    :param name: Internal effect identifier (used in presets).
    :param params: Optional list of EffectParam objects to initialize parameters.
    """

    def __init__(self, name: str, *, params: Optional[List[EffectParam]] = None):
        self.name = name
        self.params = EffectParamManager(params)

    @abstractmethod
    def apply(self, input_data: Processable) -> Processable:
        """
        Apply the effect to an image or sequence.

        :param input_data: Input image (PIL.Image, numpy.ndarray, or ImageSequence).
        :return: Processed image or sequence in the same format.
        :raises NotImplementedEffect: If not overridden in subclass.
        """

        raise NotImplementedEffect

    @property
    @abstractmethod
    def layout(self) -> Dict[str, Any]:
        """
        Declarative description of the effect's UI layout.

        :return: A dictionary describing the UI structure.
        :raises NotImplementedError: If not implemented in subclass.
        """

        raise NotImplementedError("Effect layout must be implemented in subclasses")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the effect with only parameter values.

        :return: Dictionary containing effect type, name, and parameters.
        """

        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "params": self.params.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EffectBase":
        """
        Reconstruct effect from dictionary.

        :param d: Serialized dictionary with effect data.
        :return: Restored EffectBase subclass instance.
        :raises InvalidValue: If parameter values are invalid.
        """

        effect = cls(d["name"])
        effect.params.from_dict(d.get("params", {}))
        return effect

    def set_param(self, name: str, value: Any) -> None:
        """
        Safely update a parameter value with validation.

        :param name: Parameter identifier.
        :param value: New value for the parameter.
        """

        self.params.set_parameter(name, value)

    def get_param(self, name: str) -> Any:
        """
        Get the current value of a parameter.

        :param name: Parameter identifier.
        :return: Current parameter value.
        """

        return self.params.get_parameter(name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}, params={self.params}>"