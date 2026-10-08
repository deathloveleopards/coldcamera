import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable


class ContrastBrightnessEffect(EffectBase):
    author: str = "deathloveleopards"

    def __init__(self, name="Contrast/Brightness"):
        super().__init__(
            name,
            params=[
                EffectParam("contrast", float, 1.0, default=1.0),
                EffectParam("brightness", float, 0.0, default=0.0),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        contrast = self.get_parameter("contrast")
        brightness = self.get_parameter("brightness")
        img = (img - 127.5) * contrast + 127.5 + brightness
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)
