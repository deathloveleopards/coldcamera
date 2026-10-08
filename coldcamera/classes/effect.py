from abc import ABC, abstractmethod
from typing import Any, Dict

from coldcamera.classes.parameter import EffectParam
from coldcamera.classes.parameters_manager import EffectParamManager
from coldcamera.exceptions import NotImplementedEffect
from coldcamera.types import Processable


class EffectBase(ABC):
    """
    Abstract base class for all image processing effects.

    Each effect defines parameters (via EffectParamManager) and an
    ``apply()`` method. Presentation metadata lives in the effect catalog.

    :param name: Internal effect identifier (used in presets).
    :param params: Optional mapping or sequence of EffectParam objects to initialize parameters.
    """

    def __init__(self, name: str, *, params: dict[str, EffectParam] | list[EffectParam] | tuple[EffectParam, ...] | None = None):
        """
        Initialize the effect.

        :param name: Name of the effect.
        :param params: Parameters for the effect.
        """

        self.name = name
        self.params = EffectParamManager(params)

        self.enabled = True

    @abstractmethod
    def apply(self, input_data: Processable) -> Processable:
        """
        Apply the effect to an image or sequence.

        :param input_data: Input image (PIL.Image, numpy.ndarray, or ImageSequence).
        :return: Processed image or sequence in the same format.
        :raises NotImplementedEffect: If not overridden in subclass.
        """

        raise NotImplementedEffect(f"{self.__class__.__name__} does not implement apply()")

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Serialize the effect with only parameter values.

        :return: Dictionary containing effect type, name, and parameters.
        """

        # Local import to avoid circular dependency
        from coldcamera.effects.register import get_name_for_class

        display_name = get_name_for_class(self.__class__)

        # Fallback to class name if no display name is found
        if display_name is None:
            display_name = self.__class__.__name__

        return {"type": display_name, "name": self.name, "params": self.params.to_dictionary()}

    @classmethod
    def from_dictionary(cls, d: Dict[str, Any]) -> "EffectBase":
        """
        Reconstruct effect from dictionary.

        :param d: Serialized dictionary with effect data.
        :return: Restored EffectBase subclass instance.
        :raises InvalidValue: If parameter values are invalid.
        """

        effect = cls(d["name"])
        effect.params.from_dictionary(d.get("params", {}))
        return effect

    def set_parameter(self, name: str, value: Any) -> None:
        """
        Safely update a parameter value with validation.

        :param name: Parameter identifier.
        :param value: New value for the parameter.
        """

        self.params.set_parameter(name, value)

    def get_parameter(self, name: str) -> Any:
        """
        Get the current value of a parameter.

        :param name: Parameter identifier.
        :return: Current parameter value.
        """

        return self.params.get_parameter(name)

    def __repr__(self) -> str:
        """
        Return a string representation of the effect.

        :return: String representation of the effect.
        """

        return f"<{self.__class__.__name__} name={self.name!r}, params={self.params}>"
