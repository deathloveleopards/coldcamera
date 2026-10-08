import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable


class ExposureEffect(EffectBase):
    author: str = "deathloveleopards"

    def __init__(self, name="Exposure"):
        super().__init__(
            name,
            params=[EffectParam("exposure", float, 1.0, default=1.0)],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        img *= self.get_parameter("exposure")
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)
