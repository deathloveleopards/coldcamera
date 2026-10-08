import cv2
import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable


class SharpenEffect(EffectBase):
    author: str = "deathloveleopards"

    def __init__(self, name="Sharpen"):
        super().__init__(
            name,
            params=[
                EffectParam("amount", float, 1.0, default=1.0),
                EffectParam("radius", int, 1, default=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)

        radius = int(self.get_parameter("radius"))
        if radius % 2 == 0:
            radius += 1
        blurred = cv2.GaussianBlur(img, (radius, radius), 0)

        mask = img - blurred

        sharpened = img + self.get_parameter("amount") * mask

        sharpened = np.clip(sharpened, 0, 255)
        return sharpened.astype(np.uint8)
