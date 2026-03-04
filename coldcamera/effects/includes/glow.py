import blend_modes as bm
import cv2
import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.layout import ParameterDropdown, ParameterSlider
from coldcamera.classes.parameter import EffectParam
from coldcamera.enums import BlendModeType
from coldcamera.types import Processable
from coldcamera.utils.add_alpha_channel import add_alpha_channel


class GlowEffect(EffectBase):
    author: str = "deathloveleopards"

    def __init__(self, name="Glow"):
        super().__init__(
            name,
            params=[
                EffectParam("radius", float, 5.0, default=5.0),
                EffectParam("intensity", float, 1.0, default=1.0),
                EffectParam("light_threshold", float, 0.7, default=0.7),
                EffectParam("opacity", float, 1.0, default=1.0),
                EffectParam("blend_mode", str, "lighten_only", default="lighten_only"),
            ],
            layout_elements=[
                ParameterSlider("radius", "Glow radius", min_value=0, max_value=100, step=1),
                ParameterSlider("intensity", "Glow intensity", min_value=0, max_value=5, step=0.1),
                ParameterSlider("light_threshold", "Light threshold", min_value=0, max_value=1, step=0.01),
                ParameterSlider("opacity", "Opacity", min_value=0, max_value=1, step=0.05),
                ParameterDropdown("blend_mode", "Blend mode", enum_type=BlendModeType, default=BlendModeType.NORMAL, value=BlendModeType.NORMAL),  # pyright: ignore[reportArgumentType]
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)

        radius = self.get_parameter("radius")
        intensity = self.get_parameter("intensity")
        threshold = self.get_parameter("light_threshold")

        if radius <= 0 or intensity <= 0:
            return img.astype(np.uint8)

        gray = cv2.cvtColor(img[..., :3].astype(np.uint8), cv2.COLOR_RGB2GRAY) / 255.0

        mask = (gray >= threshold).astype(np.float32)
        mask = cv2.merge([mask, mask, mask])

        bright_areas = img[..., :3] * mask

        glow_effect = cv2.GaussianBlur(bright_areas, (0, 0), sigmaX=radius, sigmaY=radius)  # pyright: ignore[reportCallIssue, reportArgumentType]

        glow_effect *= intensity

        glow_rgba = add_alpha_channel(glow_effect)
        img_rgba = add_alpha_channel(img)

        bg, fg = img_rgba / 255.0, glow_rgba / 255.0
        blend_func = getattr(bm, self.get_parameter("blend_mode"), bm.lighten_only)

        blended = blend_func(bg, fg, self.get_parameter("opacity"))
        return np.clip(blended * 255, 0, 255).astype(np.uint8)
