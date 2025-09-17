
import numpy as np
import cv2

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider, ParameterCheckBox
from application.types import Processable


class FilmGrainEffect(EffectBase):
    def __init__(self, name="Film Grain"):
        super().__init__(
            name,
            params=[
                EffectParam("grain_strength", float, 10.0, default=10.0),
                EffectParam("grain_size", float, 1.5, default=1.5),
                EffectParam("color_grain", bool, True, default=True),
            ],
            layout_elements=[
                ParameterSlider("grain_strength", "Grain Strength", min_value=0, max_value=100, step=1),
                ParameterSlider("grain_size", "Grain Size", min_value=0.5, max_value=5.0, step=0.1),
                ParameterCheckBox("color_grain", "Color Grain"),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        h, w, c = img.shape

        strength = self.get_param("grain_strength")
        size = self.get_param("grain_size")
        color_grain = self.get_param("color_grain")

        if strength <= 0:
            return img.astype(np.uint8)

        actual_strength = strength / 100.0 * 50.0

        if color_grain:
            noise = np.random.normal(0, actual_strength, (h, w, c)).astype(np.float32)
        else:
            noise_mono = np.random.normal(0, actual_strength, (h, w, 1)).astype(np.float32)
            noise = np.tile(noise_mono, (1, 1, c))

        if size > 0.0:
            downscale_factor = max(1, int(size))
            scaled_h = max(1, h // downscale_factor)
            scaled_w = max(1, w // downscale_factor)

            if color_grain:
                scaled_noise = np.random.normal(0, actual_strength, (scaled_h, scaled_w, c)).astype(np.float32)
            else:
                scaled_noise_mono = np.random.normal(0, actual_strength, (scaled_h, scaled_w, 1)).astype(np.float32)
                scaled_noise = np.tile(scaled_noise_mono, (1, 1, c))

            upscaled_noise = cv2.resize(scaled_noise, (w, h), interpolation=cv2.INTER_CUBIC)

            blur_kernel = int(size * 0.5)
            if blur_kernel % 2 == 0:
                blur_kernel += 1
            blur_kernel = max(1, blur_kernel)

            noise = cv2.GaussianBlur(upscaled_noise, (blur_kernel, blur_kernel), 0)

        processed_img = np.clip(img + noise, 0, 255).astype(np.uint8)

        return processed_img
