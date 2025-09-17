
import numpy as np
import cv2

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider, ParameterSpinBox
from application.types import Processable


class GhostingEffect(EffectBase):
    def __init__(self, name="Ghosting"):
        super().__init__(
            name,
            params=[
                EffectParam("strength", float, 0.15, default=0.15),
                EffectParam("offset_x", int, 8, default=8),
                EffectParam("offset_y", int, 4, default=4),
                EffectParam("blur_radius", int, 5, default=5),
            ],
            layout_elements=[
                ParameterSlider("strength", "Ghost strength", min_value=0.0, max_value=1.0, step=0.01),
                ParameterSpinBox("offset_x", "Offset X", min_value=-20, max_value=20, step=1),
                ParameterSpinBox("offset_y", "Offset Y", min_value=-20, max_value=20, step=1),
                ParameterSpinBox("blur_radius", "Blur radius", min_value=0, max_value=21, step=2),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)

        strength = float(self.get_param("strength"))
        offset_x = int(self.get_param("offset_x"))
        offset_y = int(self.get_param("offset_y"))
        blur_radius = int(self.get_param("blur_radius"))

        if strength <= 0:
            return img.astype(np.uint8)

        if img.shape[2] == 4:
            base = img[:, :, :3]
        else:
            base = img

        ghost = base.copy()

        ghost = np.roll(ghost, offset_y, axis=0)
        ghost = np.roll(ghost, offset_x, axis=1)

        if blur_radius % 2 == 0 and blur_radius > 0:
            blur_radius += 1
        if blur_radius == 0:
            blur_radius = 1

        ghost = cv2.GaussianBlur(ghost, (blur_radius, blur_radius), 0)

        processed = base + ghost * strength
        processed = np.clip(processed, 0, 255)

        return processed.astype(np.uint8)
