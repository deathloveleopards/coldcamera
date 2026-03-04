from typing import Any, Dict, Optional

from coldcamera.classes.layout.base import ParameterElementBase
from coldcamera.classes.layout.types import ParameterWidgetType


class ParameterSlider(ParameterElementBase):
    """Slider parameter element."""

    widget: ParameterWidgetType = ParameterWidgetType.SLIDER
    type_name: str = "param_slider"

    def __init__(self, name: str, label: str, *, default: float = 0.0, min_value: float, max_value: float, step: float = 1.0, hint: Optional[str] = None):
        """
        Initialize a slider parameter element for layout builder.

        :param name: Unique parameter identifier.
        :param label: Display name for the parameter.
        :param hint: Optional description or tooltip for the parameter.
        :param default: Default value for the slider.
        :param min_value: Minimum value for the slider.
        :param max_value: Maximum value for the slider.
        :param step: Step size for the slider.
        """

        super().__init__(name, label, hint=hint)

        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Convert the slider parameter element to a dictionary representation.

        :return: Dictionary representation of the slider parameter element.
        """

        base = self._base_dictionary()

        base.update({"min": self.min_value, "max": self.max_value, "step": self.step, "default": self.default})

        return base
