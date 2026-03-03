from typing import Any, Dict, Optional

from coldcamera.classes.layout.base import ParameterElementBase
from coldcamera.classes.layout.types import ParameterWidgetType


class ParameterCheckBox(ParameterElementBase):
    """Checkbox parameter element."""

    widget: ParameterWidgetType = ParameterWidgetType.CHECK_BOX
    type_name: str = "param_checkbox"

    def __init__(self, name: str, label: str, *, hint: Optional[str] = None, callback: Optional[str] = None):
        """
        Initialize a checkbox parameter element for layout builder.

        :param name: The name of the parameter.
        :param label: The label of the parameter.
        :param hint: An optional hint for the parameter.
        :param callback: An optional callback function for the parameter.
        """

        super().__init__(name, label, hint=hint)

        self.callback = callback

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the checkbox parameter element.

        :return: A dictionary representation of the checkbox parameter element.
        """

        base = self._base_dictionary()

        base.update({"callback": self.callback})

        return base
