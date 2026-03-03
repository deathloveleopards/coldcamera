
import numpy as np
from PIL import Image, ImageOps

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterDropdown, ParameterCheckBox
from application.types import Processable
from application.enums import RescaleResolution


class RescaleEffect(EffectBase):
    def __init__(self, name="Rescale"):
        super().__init__(
            name,
            params=[
                EffectParam("resolution", str, "640x480", default="640x480"),
                EffectParam("adaptive", bool, False, default=False),
            ],
            layout_elements=[
                ParameterDropdown(
                    "resolution",
                    "Resolution",
                    enum_type=RescaleResolution,
                    default=RescaleResolution.R640x480,
                    value=RescaleResolution.R640x480,
                ),
                ParameterCheckBox("adaptive", "Adaptive orientation"),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        resolution_code = self.get_param("resolution")
        adaptive = self.get_param("adaptive")

        try:
            w_str, h_str = resolution_code.split("x")
            target_w, target_h = int(w_str), int(h_str)
        except Exception:
            return np.array(input_data).astype(np.uint8)

        img_np = np.array(input_data).astype(np.uint8)
        h, w = img_np.shape[:2]

        if adaptive:
            img_is_portrait = h > w
            preset_is_portrait = target_h > target_w

            if img_is_portrait != preset_is_portrait:
                target_w, target_h = target_h, target_w

        pil_img = Image.fromarray(img_np)
        resized = ImageOps.contain(pil_img, (target_w, target_h))
        return np.array(resized).astype(np.uint8)
