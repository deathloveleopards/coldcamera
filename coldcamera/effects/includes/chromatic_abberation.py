import cv2
import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable


class ChromaticAberrationEffect(EffectBase):
    author: str = "deathloveleopards"

    def __init__(self, name="Chromatic Aberration"):
        super().__init__(
            name,
            params=[
                EffectParam("shift", float, 0.0, default=0.0),
                EffectParam("rotation", float, 0.0, default=0.0),
                EffectParam("ab_type", str, "rb", default="rb"),
            ],
        )

    def _shift_channel(self, channel, dx, dy):
        shifted = np.roll(channel, int(dy), axis=0)
        shifted = np.roll(shifted, int(dx), axis=1)
        return shifted

    def apply(self, input_data: Processable) -> Processable:
        shift = float(self.get_parameter("shift"))
        angle = np.deg2rad(float(self.get_parameter("rotation")))
        ab_type = self.get_parameter("ab_type")

        img = np.clip(input_data, 0, 255).astype(np.uint8)  # pyright: ignore[reportCallIssue, reportArgumentType]
        b, g, r = cv2.split(img[..., :3])

        r_new, g_new, b_new = r.copy(), g.copy(), b.copy()

        dx = np.cos(angle) * shift
        dy = np.sin(angle) * shift

        if ab_type == "rb":
            targets = {"r": r, "b": b}
        elif ab_type == "rg":
            targets = {"r": r, "g": g}
        elif ab_type == "gb":
            targets = {"g": g, "b": b}
        else:
            targets = {}

        for key, channel in targets.items():
            shifted = self._shift_channel(channel, dx, dy)
            if key == "r":
                r_new = shifted
            elif key == "g":
                g_new = shifted
            elif key == "b":
                b_new = shifted

        result = cv2.merge([b_new, g_new, r_new])
        return result.astype(np.uint8)
