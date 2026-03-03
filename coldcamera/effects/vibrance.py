
import numpy as np
import cv2

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class VibranceEffect(EffectBase):
    def __init__(self, name="Vibrance"):
        super().__init__(
            name,
            params=[
                EffectParam("vibrance", float, 0.0, default=0.0),
                EffectParam("saturation", float, 0.0, default=0.0),
            ],
            layout_elements=[
                ParameterSlider("vibrance", "Vibrance", min_value=-100, max_value=100, step=1),
                ParameterSlider("saturation", "Saturation", min_value=-100, max_value=100, step=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32) / 255.0

        vibrance_level = self.get_param("vibrance")
        saturation_level = self.get_param("saturation")

        hsv_img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv_img)

        vibrance_mult = vibrance_level / 100.0
        if vibrance_mult != 0:
            vibrance_boost = (1 - s) * 2.0
            vibrance_effect = vibrance_boost * vibrance_mult
            s_vibrance = np.clip(s + vibrance_effect, 0, 1)
        else:
            s_vibrance = s.copy()

        saturation_mult = saturation_level / 100.0
        if saturation_mult > 0:
            s_final = s_vibrance + (1 - s_vibrance) * saturation_mult
        else:
            s_final = s_vibrance + s_vibrance * saturation_mult

        s_final = np.clip(s_final, 0, 1)

        processed_hsv = cv2.merge([h, s_final, v])
        processed_rgb = cv2.cvtColor(processed_hsv, cv2.COLOR_HSV2RGB)

        return (processed_rgb * 255).astype(np.uint8)
