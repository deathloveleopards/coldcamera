
import numpy as np

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider
from application.types import Processable


class ContrastBrightnessEffect(EffectBase):
    def __init__(self, name="Contrast/Brightness"):
        super().__init__(
            name,
            params=[
                EffectParam("contrast", float, 1.0, default=1.0),
                EffectParam("brightness", float, 0.0, default=0.0),
            ],
            layout_elements=[
                ParameterSlider("contrast", "Contrast", min_value=0.5, max_value=3.0, step=0.1),
                ParameterSlider("brightness", "Brightness", min_value=-100, max_value=100, step=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        contrast = self.get_param("contrast")
        brightness = self.get_param("brightness")
        img = (img - 127.5) * contrast + 127.5 + brightness
        img = np.clip(img, 0, 255)
        return img.astype(np.uint8)