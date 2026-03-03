
import io
import numpy as np
from PIL import Image

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSpinBox
from application.types import Processable


class JpegDamageEffect(EffectBase):
    def __init__(self, name="JPEG Damage"):
        super().__init__(
            name,
            params=[
                EffectParam("quality", int, 75, default=75),
            ],
            layout_elements=[
                ParameterSpinBox("quality", "Quality", min_value=1, max_value=100, step=1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = Image.fromarray(np.array(input_data).astype(np.uint8))

        if img.mode == "RGBA":
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=self.get_param("quality"))
        buffer.seek(0)

        damaged_img = Image.open(buffer).convert("RGBA")
        return np.array(damaged_img, dtype=np.uint8)
