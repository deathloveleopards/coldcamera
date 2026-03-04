from typing import Any, Dict

from coldcamera.classes.layout.base import LayoutElementBase


class Separator(LayoutElementBase):
    """Separator element for dividing layout sections."""

    def to_dictionary(self) -> Dict[str, Any]:
        """Return a dictionary representation of the separator element.

        :return: A dictionary representation of the separator element.
        """

        return {"type": "separator"}
