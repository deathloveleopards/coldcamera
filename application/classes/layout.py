
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from application.classes.effect import EffectBase


class LayoutElementBase(ABC):
    """
    Abstract base class for all layout elements.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the element into a dictionary representation.

        :return: Dictionary containing serialized element data.
        """

        raise NotImplementedError("Subclasses must implement to_dict().")


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
        """
        Widget type associated with the parameter.

        :return: The widget type as a string.
        """

        raise NotImplementedError("Subclasses must define a widget property.")

    def _base_dict(self) -> Dict[str, Any]:
        """
        Base dictionary representation for parameters.

        :return: Dictionary containing shared parameter fields.
        """

        return {
            "type": "param",
            "name": self.name,
            "label": self.label,
            "widget": self.widget,
            "hint": self.hint,
        }


class ParameterSlider(ParameterElementBase):
    """
    Slider parameter element.

    :param name: Parameter identifier.
    :param label: Display label for the slider.
    :param min_value: Minimum slider value.
    :param max_value: Maximum slider value.
    :param step: Increment step for the slider.
    :param hint: Optional tooltip or description.
    """

    widget = "slider"

    def __init__(
        self,
        name: str,
        label: str,
        *,
        min_value: float,
        max_value: float,
        step: float = 1.0,
        hint: Optional[str] = None,
    ):
        super().__init__(name, label, hint=hint)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert slider element into dictionary.

        :return: Dictionary with slider parameters.
        """

        base = self._base_dict()
        base.update({"min": self.min_value, "max": self.max_value, "step": self.step})
        return base


class ParameterSpinBox(ParameterElementBase):
    """
    Spinbox parameter element.

    :param name: Parameter identifier.
    :param label: Display label for the spinbox.
    :param min_value: Minimum spinbox value.
    :param max_value: Maximum spinbox value.
    :param step: Increment step for the spinbox.
    :param hint: Optional tooltip or description.
    """

    widget = "spinbox"

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
        """
        Convert spinbox element into dictionary.

        :return: Dictionary with spinbox parameters.
        """

        base = self._base_dict()
        base.update({"min": self.min_value, "max": self.max_value, "step": self.step})
        return base


class ParameterCheckBox(ParameterElementBase):
    """
    Checkbox parameter element.

    :param name: Parameter identifier.
    :param label: Display label for the checkbox.
    :param hint: Optional tooltip or description.
    """

    widget = "checkbox"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert checkbox element into dictionary.

        :return: Dictionary with checkbox parameters.
        """

        return self._base_dict()


class ParameterDropdown(ParameterElementBase):
    """
    Dropdown parameter element.

    :param name: Parameter identifier.
    :param label: Display label for the dropdown.
    :param enum_type: Enum class defining available options.
    :param hint: Optional tooltip or description.
    """

    widget = "dropdown"

    def __init__(
        self,
        name: str,
        label: str,
        enum_type: Type[Enum],
        *,
        hint: Optional[str] = None,
    ):
        super().__init__(name, label, hint=hint)
        self.enum_type = enum_type

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert dropdown element into dictionary.

        :return: Dictionary with dropdown options.
        """

        base = self._base_dict()
        base.update({"options": [e.value for e in self.enum_type]})
        return base


class Separator(LayoutElementBase):
    """
    Separator element used for dividing layout sections.
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert separator into dictionary.

        :return: Dictionary with separator type.
        """

        return {"type": "separator"}


class Button(LayoutElementBase):
    """
    Button element.

    :param label: Display text for the button.
    :param icon: Optional icon name.
    :param hint: Optional tooltip or description.
    :param callback: Optional callback name associated with the button.
    """

    def __init__(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        hint: Optional[str] = None,
        callback: Optional[str] = None,
    ):
        self.label = label
        self.icon = icon
        self.hint = hint
        self.callback = callback

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert button element into dictionary.

        :return: Dictionary with button parameters.
        """

        return {
            "type": "button",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "callback": self.callback,
        }


class Group(LayoutElementBase):
    """
    Group element containing multiple sub-elements.

    :param label: Display label for the group.
    :param icon: Optional icon name.
    :param hint: Optional tooltip or description.
    :param items: List of layout elements contained in the group.
    """

    def __init__(
        self,
        label: str,
        *,
        icon: Optional[str] = None,
        hint: Optional[str] = None,
        items: Optional[List[LayoutElementBase]] = None,
    ):
        self.label = label
        self.icon = icon
        self.hint = hint
        self.items = items or []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert group element into dictionary.

        :return: Dictionary with group parameters and nested items.
        """

        return {
            "type": "group",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "items": [i.to_dict() for i in self.items],
        }


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

    def __init__(
        self,
        parent: "EffectBase",
        name: str,
        *,
        icon: Optional[str] = None,
        hint: Optional[str] = None,
        elements: Optional[List[LayoutElementBase]] = None,
    ):
        self.parent = parent
        self.name = name
        self.icon = icon
        self.hint = hint
        self.elements = elements or []
        self._callbacks: Dict[str, Callable] = {}

    def callback(self, name: str) -> Callable:
        """
        Instance-level decorator for registering callbacks.

        Example:
            layout = EffectLayout(...)
            @layout.callback("reset")
            def _reset(effect, *args): ...
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
        :raises KeyError: If callback not registered.
        """

        if name not in self._callbacks:
            raise KeyError(f"No callback registered for {name}")
        return self._callbacks[name](self.parent, *args, **kwargs)

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