from collections.abc import Sequence
from enum import Enum
from typing import List, Optional, TypeAlias

from coldcamera.classes.layout import LayoutElementBase
from coldcamera.classes.parameter import EffectParam

EffectParams: TypeAlias = Optional[List[EffectParam]]
LayoutElements: TypeAlias = Optional[Sequence[LayoutElementBase]]


class ParameterWidgetType(Enum):
    SLIDER = "slider"
    SPIN_BOX = "spin_box"
    CHECK_BOX = "check_box"
    DROPDOWN = "dropdown"
