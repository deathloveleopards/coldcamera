
import numpy as np
import cv2

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class HueEffect(EffectBase):
    def __init__(self, name="HUE"):
        super().__init__(
            name,
            params=[
                EffectParam("hue_shift", float, 0.0, default=0.0),
            ],
            layout_elements=[
                ParameterSlider("hue_shift", "Shift", min_value=-180.0, max_value=180.0, step=1.0),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.uint8)

        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)

        hue_shift = self.get_param("hue_shift")
        hsv[..., 0] = (hsv[..., 0] + (hue_shift / 2)) % 180

        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        return result
