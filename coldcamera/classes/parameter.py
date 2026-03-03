
from typing import Optional, List, Dict, Any, Type, Union
from enum import Enum

from application.exceptions import InvalidValue


class EffectParam:
    """
    A single parameter of an effect, supporting validation and serialization.

    :param name: Internal parameter identifier (used in code and presets).
    :param param_type: The expected type of the parameter. Can be:
                       - A native Python type (int, float, str, bool)
                       - An Enum subclass
    :param value: Current value of the parameter.
    :param default: Default value for reset or initialization.
    """

    name: str
    param_type: Union[Type, Type[Enum]]
    value: Any
    default: Optional[Any]

    def __init__(
        self,
        name: str,
        param_type: Union[Type, Type[Enum]],
        value: Any,
        *,
        default: Optional[Any] = None,
    ):
        """
        Initialize an EffectParam.

        :param name: Internal parameter identifier.
        :param param_type: Expected type of the parameter (Python type or Enum subclass).
        :param value: Initial value of the parameter.
        :param default: Default value if provided, otherwise falls back to ``value``.
        """

        self.name = name
        self.param_type = param_type
        self.default = default if default is not None else value
        self.value = self.validate(value)

    def validate(self, value: Any) -> Any:
        """
        Validate a value against the parameter type.

        :param value: Value to validate.
        :return: The validated and possibly converted value.
        :raises InvalidValue: If the value does not match the expected type or enum options.
        """

        if isinstance(self.param_type, type) and issubclass(self.param_type, Enum):
            if isinstance(value, self.param_type):
                return value
            try:
                return self.param_type(value)
            except ValueError:
                raise InvalidValue(
                    f"{self.name} must be one of: {[e.value for e in self.param_type]}"
                )

        if not isinstance(value, self.param_type):
            raise InvalidValue(f"{self.name} must be of type {self.param_type.__name__}")

        return value

    def set_value(self, value: Any) -> None:
        """
        Set and validate the parameter value.

        :param value: New value to assign.
        :raises InvalidValue: If the value does not match the expected type.
        """

        self.value = self.validate(value)

    def get_value(self) -> Any:
        """
        Get the current parameter value.

        :return: The current value.
        """

        return self.value

    def get_options(self) -> Optional[List[Any]]:
        """
        Get possible options if the parameter type is an Enum.

        :return: List of possible enum values, or ``None`` if not an Enum.
        """

        if isinstance(self.param_type, type) and issubclass(self.param_type, Enum):
            return [e.value for e in self.param_type]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the parameter to a dictionary-like representation.

        :return: Serialized value (enum values are stored by their underlying value).
        """

        if isinstance(self.value, Enum):
            return self.value.value
        return self.value

    @classmethod
    def from_dict(cls, name: str, value: Any, definition: "EffectParam") -> "EffectParam":
        """
        Restore an EffectParam from serialized data.

        :param name: Parameter identifier.
        :param value: Serialized value to restore.
        :param definition: Existing EffectParam definition to update.
        :return: The updated EffectParam instance.
        """

        definition.set_value(value)
        return definition

    def __repr__(self) -> str:
        """
        String representation of the EffectParam.

        :return: A string in the form "<EffectParam name=value (type)>".
        """

        return f"<EffectParam {self.name}={self.value!r} ({self.param_type})>"
