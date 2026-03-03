from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from coldcamera.classes.layout.types import ParameterWidgetType


class LayoutElementBase(ABC):
    """Abstract base class for all layout elements."""

    @abstractmethod
    def to_dictionary(self) -> Dict[str, Any]:
        """
        Convert the element into a dictionary representation.

        :return: Dictionary containing serialized element data.
        :raises NotImplementedError: If subclass does not implement this method.
        """

        raise NotImplementedError("Subclasses must implement to_dictionary().")


class ParameterElementBase(LayoutElementBase, ABC):
    """
    Abstract base class for parameter layout elements.

    :param name: Unique parameter identifier.
    :param label: Display name for the parameter.
    :param hint: Optional description or tooltip for the parameter.
    :param widget: Widget type associated with the parameter.
    :param type_name: More specific type identifier for the parameter element.
    """

    name: str
    label: str
    hint: Optional[str]

    widget: ParameterWidgetType
    type_name: str

    def __init__(self, name: str, label: str, *, hint: Optional[str] = None):
        self.name = name
        self.label = label
        self.hint = hint

    def _base_dictionary(self) -> Dict[str, Any]:
        """Base dictionary representation for parameters."""

        return {
            "type": self.type_name,
            "name": self.name,
            "label": self.label,
            "widget": self.widget,
            "hint": self.hint,
        }
