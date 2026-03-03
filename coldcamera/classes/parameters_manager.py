
from typing import Optional, Union, Dict, List, Any

from application.classes.parameter import EffectParam
from application.exceptions import InvalidValue


class EffectParamManager:
    """
    Container for managing effect parameters.

    Provides safe access, modification, and (de)serialization of parameters.

    :param params: Optional initial parameters, either:
                   - dict[str, EffectParam]
                   - list[EffectParam]
    """

    def __init__(self, params: Optional[Union[Dict[str, EffectParam], List[EffectParam]]] = None):
        self._params: Dict[str, EffectParam] = {}
        if isinstance(params, dict):
            self._params = params
        elif isinstance(params, list) or isinstance(params, tuple):
            self._params = {p.name: p for p in params}

    def add_parameter(self, param: EffectParam) -> None:
        """Add a new parameter to the manager."""

        self._params[param.name] = param

    def get_parameter(self, name: str) -> Any:
        """
        Get the current value of a parameter.

        :param name: Parameter identifier.
        :return: Current value of the parameter.
        :raises KeyError: If parameter with given name does not exist.
        """

        if name not in self._params:
            raise KeyError(f"Unknown parameter: {name}")
        return self._params[name].get_value()

    def set_parameter(self, name: str, value: Any) -> None:
        """
        Update a parameter value with validation.

        :param name: Parameter identifier.
        :param value: New parameter value.
        :raises KeyError: If parameter with given name does not exist.
        """

        if name not in self._params:
            raise KeyError(f"Unknown parameter: {name}")
        self._params[name].set_value(value)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize all parameters to a dictionary."""

        return {k: v.to_dict() for k, v in self._params.items()}

    def from_dict(self, d: Dict[str, Any]) -> None:
        """
        Restore parameters from a dictionary.

        :param d: Dictionary of serialized parameters.
        :raises InvalidValue: If parameter values are invalid.
        """

        for k, v in d.items():
            if k in self._params:
                try:
                    self._params[k] = EffectParam.from_dict(k, v, self._params[k])
                except InvalidValue as e:
                    raise InvalidValue(f"Invalid value for param '{k}': {e}")

    def __getitem__(self, name: str) -> EffectParam:
        return self._params[name]

    def __iter__(self):
        return iter(self._params.items())

    def __repr__(self) -> str:
        params_str = ", ".join(f"{k}={v.get_value()!r}" for k, v in self._params.items())
        return f"<EffectParamManager {params_str}>"