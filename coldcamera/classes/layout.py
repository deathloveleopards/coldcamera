
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from application.classes.effect import EffectBase


# ------------------------
# Base layout elements
# ------------------------
class LayoutElementBase(ABC):
    """Abstract base class for all layout elements."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the element into a dictionary representation.

        :return: Dictionary containing serialized element data.
        :raises NotImplementedError: If subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement to_dict().")


# ------------------------
# Parameter elements
# ------------------------
class ParameterElementBase(LayoutElementBase, ABC):
    """
    Abstract base class for parameter layout elements.

    :param name: Unique parameter identifier.
    :param label: Display name for the parameter.
    :param hint: Optional description or tooltip for the parameter.
    """

    name: str
    label: str
    hint: str

    def __init__(self, name: str, label: str, *, hint: Optional[str] = None):
        self.name = name
        self.label = label
        self.hint = hint

    @property
    @abstractmethod
    def widget(self) -> str:
        """Widget type associated with the parameter."""
        pass

    @property
    @abstractmethod
    def type_name(self) -> str:
        """More specific type identifier for the parameter element."""
        pass

    def _base_dict(self) -> Dict[str, Any]:
        """Base dictionary representation for parameters."""
        return {
            "type": self.type_name,
            "name": self.name,
            "label": self.label,
            "widget": self.widget,
            "hint": self.hint,
        }


class ParameterSlider(ParameterElementBase):
    """Slider parameter element."""

    widget = "slider"
    type_name = "param_slider"

    def __init__(
        self,
        name: str,
        label: str,
        *,
        default: float = 0.0,
        min_value: float,
        max_value: float,
        step: float = 1.0,
        hint: Optional[str] = None,
    ):
        super().__init__(name, label, hint=hint)
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dict(self) -> Dict[str, Any]:
        base = self._base_dict()
        base.update({
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "default": self.default
        })
        return base


class ParameterSpinBox(ParameterElementBase):
    """Spinbox parameter element."""

    widget = "spinbox"
    type_name = "param_spinbox"

    def __init__(
        self,
        name: str,
        label: str,
        *,
        min_value: int,
        max_value: int,
        step: int = 1,
        hint: Optional[str] = None,
    ):
        super().__init__(name, label, hint=hint)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dict(self) -> Dict[str, Any]:
        base = self._base_dict()
        base.update({
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step
        })
        return base


class ParameterCheckBox(ParameterElementBase):
    """Checkbox parameter element."""

    widget = "checkbox"
    type_name = "param_checkbox"

    def __init__(self, name: str, label: str, *, hint: Optional[str] = None, callback: Optional[str] = None):
        super().__init__(name, label, hint=hint)
        self.callback = callback

    def to_dict(self) -> Dict[str, Any]:
        base = self._base_dict()
        base.update({"callback": self.callback})
        return base


class ParameterDropdown(ParameterElementBase):
    """Dropdown parameter element."""

    widget = "dropdown"
    type_name = "param_dropdown"

    def __init__(
        self,
        name: str,
        label: str,
        enum_type: Type[Enum],
        value: Type[Enum],
        default: Type[Enum],
        *,
        hint: Optional[str] = None,
    ):
        super().__init__(name, label, hint=hint)
        self.enum_type = enum_type
        self.value = value
        self.default = default if default is not None else value

    def to_dict(self) -> Dict[str, Any]:
        base = self._base_dict()
        base.update({
            "options": [e.label for e in self.enum_type],
            "values": [e.code for e in self.enum_type],
            "default": self.default.label if self.default else None,
            "value": self.value.label if self.value else None,
        })
        return base


# ------------------------
# Layout helpers
# ------------------------
class Separator(LayoutElementBase):
    """Separator element for dividing layout sections."""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "separator"}


class Button(LayoutElementBase):
    """Button element."""

    def __init__(self, label: str, *, icon: Optional[str] = None,
                 hint: Optional[str] = None, callback: Optional[str] = None):
        self.label = label
        self.icon = icon
        self.hint = hint
        self.callback = callback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "button",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "callback": self.callback,
        }


class Group(LayoutElementBase):
    """Group element containing multiple sub-elements."""

    def __init__(self, label: str, *, icon: Optional[str] = None,
                 hint: Optional[str] = None, items: Optional[List[LayoutElementBase]] = None):
        self.label = label
        self.icon = icon
        self.hint = hint
        self.items = items or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "group",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "items": [i.to_dict() for i in self.items],
        }


# ------------------------
# Effect layout container
# ------------------------
class EffectLayout:
    """
    Layout container for building and serializing effect layouts.

    Holds UI elements, links them to the parent effect,
    and manages callbacks bound via decorators.

    :param parent: Parent EffectBase instance that owns this layout.
    :param name: Name of the effect.
    :param icon: Optional icon representing the effect.
    :param hint: Optional tooltip or description.
    :param elements: List of layout elements in the effect.
    """

    def __init__(self, parent: "EffectBase", name: str, *,
                 icon: Optional[str] = None, hint: Optional[str] = None,
                 elements: Optional[List[LayoutElementBase]] = None):
        self.parent = parent
        self.name = name
        self.icon = icon
        self.hint = hint
        self.elements = elements or []
        self._callbacks: Dict[str, Callable] = {}

    # ------------------------
    # Callback management
    # ------------------------
    def callback(self, name: str) -> Callable:
        """
        Instance-level decorator for registering callbacks.

        :param name: Name of the callback.
        :return: Decorator function that registers the callback.
        """

        def decorator(func: Callable):
            self._callbacks[name] = func
            return func

        return decorator

    def trigger(self, name: str, *args, **kwargs):
        """
        Trigger a registered callback by name.

        :param name: Callback name to invoke.
        :param args: Positional arguments passed to callback.
        :param kwargs: Keyword arguments passed to callback.
        :return: Result of the callback function.
        :raises KeyError: If callback not registered.
        """
        if name not in self._callbacks:
            raise KeyError(f"No callback registered for {name}")
        return self._callbacks[name](self.parent, *args, **kwargs)

    # ------------------------
    # Layout serialization
    # ------------------------
    def build(self) -> Dict[str, Any]:
        """
        Build the complete layout structure.

        :return: Dictionary representation of the layout.
        """
        return {
            "effect": {
                "name": self.name,
                "icon": self.icon,
                "hint": self.hint,
            },
            "layout": [el.to_dict() for el in self.elements],
        }
