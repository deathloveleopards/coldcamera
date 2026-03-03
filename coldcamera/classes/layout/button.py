from typing import Any, Dict, Optional

from coldcamera.classes.layout.base import LayoutElementBase


class Button(LayoutElementBase):
    """Button element."""

    def __init__(self, label: str, *, icon: Optional[str] = None, hint: Optional[str] = None, callback: Optional[str] = None):
        """
        Initialize a button element for the layout builder.

        :param label: The label of the button.
        :param icon: The icon of the button.
        :param hint: The hint of the button.
        :param callback: The callback of the button.
        """

        self.label = label
        self.icon = icon
        self.hint = hint
        self.callback = callback

    def to_dictionary(self) -> Dict[str, Any]:
        """Return a dictionary representation of the button element.

        :return: A dictionary representation of the button element.
        """

        return {
            "type": "button",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "callback": self.callback,
        }
