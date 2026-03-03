
import numpy as np
import blend_modes as bm

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider, ParameterDropdown
from application.utils.add_alpha_channel import add_alpha_channel
from application.enums import BlendModeType, NoiseType
from application.types import Processable


class NoiseEffect(EffectBase):
    def __init__(self, name="Noise"):
        super().__init__(
            name,
            params=[
                EffectParam("strength", float, 0.0, default=0.0),
                EffectParam("opacity", float, 1.0, default=1.0),
                EffectParam("type", str, "gaussian", default="gaussian"),
                EffectParam("blend_mode", str, "lighten_only", default="lighten_only"),
            ],
            layout_elements=[
                ParameterSlider("strength", "Noise strength", min_value=0, max_value=100, step=1),
                ParameterSlider("opacity", "Opacity", min_value=0, max_value=1, step=0.05),
                ParameterDropdown("type", "Noise type", enum_type=NoiseType,
                                  default=NoiseType.GAUSSIAN,
                                  value=NoiseType.GAUSSIAN),
                ParameterDropdown("blend_mode", "Blend mode", enum_type=BlendModeType,
                                  default=BlendModeType.LIGHTEN_ONLY,
                                  value=BlendModeType.LIGHTEN_ONLY),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        noise_param = self.get_param("strength")
        if noise_param <= 0:
            return img.astype(np.uint8)

        h, w = img.shape[:2]
        noise_rgb = np.zeros((h, w, 3), dtype=np.float32)
        noise_type = self.get_param("type")

        if noise_type == "gaussian":
            noise_rgb = np.random.normal(0, noise_param, (h, w, 3)).astype(np.float32)
        elif noise_type == "salt":
            density = np.clip(noise_param / 100.0, 0.0, 1.0)
            num_pixels = int(density * h * w)
            row_coords = np.random.randint(0, h, num_pixels)
            col_coords = np.random.randint(0, w, num_pixels)
            noise_rgb[row_coords, col_coords, :] = 255
        elif noise_type == "pepper":
            density = np.clip(noise_param / 100.0, 0.0, 1.0)
            num_pixels = int(density * h * w)
            row_coords = np.random.randint(0, h, num_pixels)
            col_coords = np.random.randint(0, w, num_pixels)
            noise_rgb[row_coords, col_coords, :] = 0
        elif noise_type == "speckle":
            speckle_strength = noise_param / 255.0
            random_factor = np.random.normal(0, speckle_strength, (h, w, 3)).astype(np.float32)
            noise_rgb = img[..., :3] * random_factor

        noise_rgba = add_alpha_channel(noise_rgb)
        img_rgba = add_alpha_channel(img)

        bg, fg = img_rgba / 255.0, noise_rgba / 255.0
        blend_func = getattr(bm, self.get_param("blend_mode"), bm.normal)
        blended = blend_func(bg, fg, self.get_param("opacity"))
        return (blended * 255).astype(np.uint8)