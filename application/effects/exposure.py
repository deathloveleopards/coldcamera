
import numpy as np

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class ExposureEffect(EffectBase):
    def __init__(self, name="Exposure"):
        super().__init__(
            name,
            params=[
                EffectParam("exposure", float, 1.0, default=1.0),
            ],
            layout_elements=[
                ParameterSlider("exposure", "Exposure", min_value=0.5, max_value=2.0, step=0.05),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        img *= self.get_param("exposure")
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)

