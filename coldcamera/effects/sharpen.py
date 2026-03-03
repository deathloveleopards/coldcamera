
import numpy as np
import cv2

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class SharpenEffect(EffectBase):
    def __init__(self, name="Sharpen"):
        super().__init__(
            name,
            params=[
                EffectParam("amount", float, 1.0, default=1.0),
                EffectParam("radius", int, 1, default=1),
            ],
            layout_elements=[
                ParameterSlider("amount", "Amount", min_value=0.0, max_value=3.0, step=0.1),
                ParameterSlider("radius", "Radius", min_value=1, max_value=10, step=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)

        radius = int(self.get_param("radius"))
        if radius % 2 == 0:
            radius += 1
        blurred = cv2.GaussianBlur(img, (radius, radius), 0)

        mask = img - blurred

        sharpened = img + self.get_param("amount") * mask

        sharpened = np.clip(sharpened, 0, 255)
        return sharpened.astype(np.uint8)
