from typing import Any, Dict, Optional

from coldcamera.classes.layout.base import ParameterElementBase
from coldcamera.classes.layout.types import ParameterWidgetType


class ParameterSpinBox(ParameterElementBase):
    """Spinbox parameter element."""

    widget: ParameterWidgetType = ParameterWidgetType.SPIN_BOX
    type_name: str = "param_spinbox"

    def __init__(self, name: str, label: str, *, min_value: int, max_value: int, step: int = 1, hint: Optional[str] = None):
        """
        Initialize a spinbox parameter element for layout builder.

        :param name: The name of the parameter.
        :param label: The label of the parameter.
        :param min_value: The minimum value of the spinbox.
        :param max_value: The maximum value of the spinbox.
        :param step: The step size of the spinbox.
        :param hint: An optional hint for the parameter.
        """

        super().__init__(name, label, hint=hint)

        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the spinbox parameter element.

        :return: A dictionary representation of the spinbox parameter element.
        """

        base = self._base_dictionary()

        base.update({"min": self.min_value, "max": self.max_value, "step": self.step})

        return base
