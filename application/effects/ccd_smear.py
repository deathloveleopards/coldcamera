
import numpy as np
import cv2
import random

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider, ParameterCheckBox
from application.types import Processable


class CCDSmearEffect(EffectBase):
    def __init__(self, name="CCD Smear"):
        super().__init__(
            name,
            params=[
                EffectParam("smear_threshold", int, 220, default=220),
                EffectParam("smear_strength", float, 0.3, default=0.3),
                EffectParam("smear_h_blur", int, 3, default=3),
                EffectParam("smear_color_r", int, 255, default=255),
                EffectParam("smear_color_g", int, 255, default=255),
                EffectParam("smear_color_b", int, 200, default=200),
                EffectParam("smear_falloff", float, 0.8, default=0.8),
                EffectParam("use_mask", bool, False, default=False),
            ],
            layout_elements=[
                ParameterSlider("smear_threshold", "Threshold", min_value=0, max_value=255, step=1),
                ParameterSlider("smear_strength", "Smear Strength", min_value=0.0, max_value=1.0, step=0.01),
                ParameterSlider("smear_h_blur", "Horizontal Blur", min_value=0, max_value=21, step=2),
                ParameterSlider("smear_color_r", "Smear Color R", min_value=0, max_value=255, step=1),
                ParameterSlider("smear_color_g", "Smear Color G", min_value=0, max_value=255, step=1),
                ParameterSlider("smear_color_b", "Smear Color B", min_value=0, max_value=255, step=1),
                ParameterSlider("smear_falloff", "Smear Falloff", min_value=0.0, max_value=1.0, step=0.01),
                ParameterCheckBox("use_mask", "Use Mask"),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:
        img = np.array(input_data).astype(np.float32)
        if img.shape[-1] == 4:
            img_rgb = img[:, :, :3]
        else:
            img_rgb = img

        h, w, _ = img_rgb.shape

        threshold = self.get_param("smear_threshold")
        smear_strength = self.get_param("smear_strength")
        smear_h_blur = self.get_param("smear_h_blur")
        smear_color = (
            self.get_param("smear_color_r"),
            self.get_param("smear_color_g"),
            self.get_param("smear_color_b"),
        )
        smear_falloff = self.get_param("smear_falloff")
        use_mask = self.get_param("use_mask")

        img_gray = cv2.cvtColor(img_rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        _, bright_pixels_mask = cv2.threshold(img_gray, threshold, 255, cv2.THRESH_BINARY)

        smear_layer = np.zeros_like(img_rgb, dtype=np.float32)

        for col in range(w):
            bright_rows = np.where(bright_pixels_mask[:, col] > 0)[0]
            if len(bright_rows) > 0:
                smear_base_color = np.array(smear_color, dtype=float)
                smear_col = np.full((h, 3), smear_base_color * smear_strength, dtype=np.float32)

                if smear_h_blur > 0 and smear_h_blur % 2 != 0:
                    smear_col = cv2.GaussianBlur(smear_col, (smear_h_blur, 1), 0)

                center_y = bright_rows.mean()
                falloff_mask = np.exp(-((np.arange(h) - center_y) / (h * smear_falloff / 2))**2)
                smear_col *= falloff_mask.reshape(h, 1)

                if use_mask:
                    angle = random.uniform(0, np.pi)
                    cos_a, sin_a = np.cos(angle), np.sin(angle)
                    y_coords_norm = np.linspace(-1, 1, h).reshape(-1, 1)
                    gradient = np.abs(y_coords_norm * sin_a + (random.random() * 2 - 1) * cos_a * 0.1)
                    gradient = np.clip(1 - gradient, 0, 1)
                    smear_col *= gradient

                smear_layer[:, col, :] = smear_col

        processed_img = np.clip(img_rgb + smear_layer, 0, 255).astype(np.uint8)
        return processed_img
