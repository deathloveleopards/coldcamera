
import numpy as np

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class WarmthEffect(EffectBase):
    def __init__(self, name="Warmth"):
        super().__init__(
            name,
            params=[
                EffectParam("warmth", float, 0.0, default=0.0),
            ],
            layout_elements=[
                ParameterSlider("warmth", "Warmth", min_value=-50, max_value=50, step=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        warmth_val = self.get_param("warmth") / 100.0
        img[..., 0] *= (1.0 + warmth_val)  # reduce blue
        img[..., 2] *= (1.0 - warmth_val)  # increase red
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)