from typing import Any, Dict, List, Optional

from coldcamera.classes.layout.base import LayoutElementBase


class Group(LayoutElementBase):
    """Group element containing multiple sub-elements."""

    def __init__(self, label: str, *, icon: Optional[str] = None, hint: Optional[str] = None, items: Optional[List[LayoutElementBase]] = None):
        """
        Initialize a Group element.

        :param label: The label for the group.
        :param icon: Optional icon for the group.
        :param hint: Optional hint for the group.
        :param items: Optional list of sub-elements.
        """

        self.label = label
        self.icon = icon
        self.hint = hint
        self.items = items or []

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Convert the group to a dictionary representation.

        :return: A dictionary representation of the group.
        """

        return {
            "type": "group",
            "label": self.label,
            "icon": self.icon,
            "hint": self.hint,
            "items": [i.to_dictionary() for i in self.items],
        }
