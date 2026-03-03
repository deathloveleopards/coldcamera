from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from coldcamera.classes.layout.types import LayoutElements

if TYPE_CHECKING:
    from coldcamera.classes.effect import EffectBase


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

    def __init__(self, parent: "EffectBase", name: str, *, icon: Optional[str] = None, hint: Optional[str] = None, elements: LayoutElements = None):
        self.parent = parent
        self.name = name
        self.icon = icon
        self.hint = hint
        self.elements = elements or []
        self._callbacks: Dict[str, Callable] = {}

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

    def build(self) -> Dict[str, Any]:
        """
        Build the complete layout structure.

        :return: Dictionary representation of the layout.
        """

        return {
            "effect": {"name": self.name, "icon": self.icon, "hint": self.hint},
            "layout": [el.to_dictionary() for el in self.elements],
        }
