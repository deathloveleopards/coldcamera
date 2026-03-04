from enum import Enum
from typing import Any, Dict, Optional, Type

from coldcamera.classes.layout.base import ParameterElementBase
from coldcamera.classes.layout.types import ParameterWidgetType


class ParameterDropdown(ParameterElementBase):
    """Dropdown parameter element."""

    widget: ParameterWidgetType = ParameterWidgetType.DROPDOWN
    type_name: str = "param_dropdown"

    def __init__(self, name: str, label: str, enum_type: Type[Enum], value: Type[Enum], default: Type[Enum], *, hint: Optional[str] = None):
        """
        Initialize a dropdown parameter element for layout builder.

        :param name: The name of the parameter.
        :param label: The label of the parameter.
        :param enum_type: The enum type of the parameter.
        :param value: The current value of the parameter.
        :param default: The default value of the parameter.
        :param hint: An optional hint for the parameter.
        """

        super().__init__(name, label, hint=hint)

        self.enum_type = enum_type
        self.value = value
        self.default = default if default is not None else value

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the dropdown parameter element.

        :return: A dictionary representation of the dropdown parameter element.
        """

        base = self._base_dictionary()

        base.update(
            {
                "options": [e.label for e in self.enum_type],  # pyright: ignore[reportAttributeAccessIssue]
                "values": [e.code for e in self.enum_type],  # pyright: ignore[reportAttributeAccessIssue]
                "default": self.default.label if self.default else None,  # pyright: ignore[reportAttributeAccessIssue]
                "value": self.value.label if self.value else None,  # pyright: ignore[reportAttributeAccessIssue]
            }
        )

        return base
