from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from coldcamera.classes.layout import EffectLayout
from coldcamera.classes.parameters_manager import EffectParamManager
from coldcamera.exceptions import NotImplementedEffect
from coldcamera.types import EffectParams, LayoutElements, Processable


class EffectBase(ABC):
    """
    Abstract base class for all image processing effects.

    Each effect defines a set of parameters (via EffectParamManager),
    provides an `apply()` method for rendering, and a declarative
    `layout` description for building UI components.

    :param name: Internal effect identifier (used in presets).
    :param params: Optional list of EffectParam objects to initialize parameters.
    :param layout_elements: Optional list of layout elements to build the UI.
    :param icon: Optional icon for representing the effect in UI.
    :param hint: Optional description or tooltip for the effect.
    """

    _class_callbacks: Dict[str, Callable] = {}

    @classmethod
    def callback(cls, name: str) -> Callable:
        """
        Class-level decorator for binding layout callbacks.

        Example:
            class BlurEffect(EffectBase):
                @EffectBase.callback("apply_blur")
                def _on_apply(self, *args, **kwargs):
                    ...

        :param name: Name of the callback to register.
        :return: Decorator function that binds the callback.
        """

        def decorator(func: Callable):
            cls._class_callbacks[name] = func
            return func

        return decorator

    def __init__(
        self, name: str, *, params: EffectParams = None, layout_elements: LayoutElements = None, icon: Optional[str] = None, hint: Optional[str] = None
    ):
        self.name = name
        self.params = EffectParamManager(params)

        # Initialize layout with reference to this effect
        self.layout = EffectLayout(parent=self, name=name, icon=icon, hint=hint, elements=layout_elements)

        self.enabled = True

        # Bind class-level callbacks to this instance
        for cb_name, func in self._class_callbacks.items():
            self.layout._callbacks[cb_name] = func.__get__(self, self.__class__)

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

        return {"type": display_name, "name": self.name, "params": self.params.to_dict()}

    @classmethod
    def from_dictionary(cls, d: Dict[str, Any]) -> "EffectBase":
        """
        Reconstruct effect from dictionary.

        :param d: Serialized dictionary with effect data.
        :return: Restored EffectBase subclass instance.
        :raises InvalidValue: If parameter values are invalid.
        """

        effect = cls(d["name"])
        effect.params.from_dict(d.get("params", {}))
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
