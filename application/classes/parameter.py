
from typing import Optional, List, Dict, Callable, Any

from application.types import ParamType
from application.exceptions import InvalidValue


class EffectParam:
    """
    A single parameter of an effect, including metadata for GUI generation,
    serialization for presets, and optional localization hints.

    :param name: Internal parameter identifier (used in code and presets).
    :param label: Human-readable label for UI display (localizable).
    :param param_type: The type of parameter, determines the widget to be generated.
                       Can be one of: "int_slider", "int_spinbox",
                       "float_slider", "float_spinbox",
                       "bool", "button", "enum", "string".
    :param value: Current value of the parameter.
    :param default: Default value for reset or initialization.
    :param minimum: Minimum allowed value (for numeric parameters).
    :param maximum: Maximum allowed value (for numeric parameters).
    :param step: Step size for sliders/spinboxes.
    :param options: List of options (for enum type).
    :param callback: Optional callback function (for button type).
    :param hint: Optional tooltip or additional description (localizable).
    """

    name: str
    label: str
    param_type: ParamType
    value: Any
    default: Optional[Any]
    minimum: Optional[float]
    maximum: Optional[float]
    step: Optional[float]
    options: Optional[List[str]]
    callback: Optional[Callable[[], None]]
    hint: Optional[str]

    def __init__(
        self,
        name: str,
        label: str,
        param_type: ParamType,
        *,
        value: Any,
        default: Optional[Any] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        step: Optional[float] = None,
        options: Optional[List[str]] = None,
        callback: Optional[Callable[[], None]] = None,
        hint: Optional[str] = None
    ):
        self.name = name
        self.label = label
        self.param_type: ParamType = param_type
        self.default = default if default is not None else value
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.options = options or []
        self.callback = callback
        self.hint = hint

        # validate initial value
        self.value = self.validate(value)

    def validate(self, value: Any) -> Any:
        if self.param_type in {"int_slider", "int_spinbox"}:
            if not isinstance(value, int):
                raise InvalidValue(f"{self.name} must be int, got {type(value).__name__}")
            if self.minimum is not None and value < self.minimum:
                raise InvalidValue(f"{self.name} below minimum {self.minimum}")
            if self.maximum is not None and value > self.maximum:
                raise InvalidValue(f"{self.name} above maximum {self.maximum}")

        elif self.param_type in {"float_slider", "float_spinbox"}:
            if not isinstance(value, (int, float)):
                raise InvalidValue(f"{self.name} must be float, got {type(value).__name__}")
            if self.minimum is not None and value < self.minimum:
                raise InvalidValue(f"{self.name} below minimum {self.minimum}")
            if self.maximum is not None and value > self.maximum:
                raise InvalidValue(f"{self.name} above maximum {self.maximum}")

        elif self.param_type == "enum":
            if value not in self.options:
                raise InvalidValue(f"{self.name} must be one of {self.options}, got {value}")

        elif self.param_type == "bool":
            if not isinstance(value, bool):
                raise InvalidValue(f"{self.name} must be bool, got {type(value).__name__}")

        elif self.param_type == "string":
            if not isinstance(value, str):
                raise InvalidValue(f"{self.name} must be string, got {type(value).__name__}")

        elif self.param_type == "button":
            return None

        return value

    def set_value(self, value: Any) -> None:
        self.value = self.validate(value)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize parameter to a dictionary for preset storage."""
        return self.value

    @classmethod
    def from_dict(cls, name: str, value: Any, definition: "EffectParam") -> "EffectParam":
        """Restore parameter from serialized dictionary."""
        definition.set_value(value)
        return definition

    def __repr__(self) -> str:
        return f"<EffectParam {self.name}={self.value!r} ({self.param_type})>"
