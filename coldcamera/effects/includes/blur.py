import blend_modes as bm
import numpy as np

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.parameter import EffectParam
from coldcamera.classes.shader_processor import ShaderProcessorBase
from coldcamera.types import Processable
from coldcamera.utils.add_alpha_channel import add_alpha_channel


class BlurShaderProcessor(ShaderProcessorBase):
    author: str = "deathloveleopards"

    def fragment_shader(self) -> str:
        return """
        #version 330 core
        uniform sampler2D tDiffuse;
        uniform float amount;
        uniform float angle;
        in vec2 vUv;
        out vec4 fragColor;

        const int NUM_SAMPLES = 32;

        void main() {
            vec2 texSize = textureSize(tDiffuse, 0);
            vec2 dir = vec2(cos(angle), sin(angle)) / texSize;

            vec4 sum = vec4(0.0);
            float halfRange = amount * 0.5;

            for (int i = 0; i < NUM_SAMPLES; i++) {
                float t = float(i) / float(NUM_SAMPLES - 1);
                float offset = mix(-halfRange, halfRange, t);
                sum += texture(tDiffuse, vUv + dir * offset);
            }

            fragColor = sum / float(NUM_SAMPLES);
        }
        """

    def set_uniforms(self, **kwargs):
        self.prog["amount"].value = float(kwargs.get("amount", 0.0))  # pyright: ignore[reportAttributeAccessIssue]
        self.prog["angle"].value = float(kwargs.get("angle", 0.0))  # pyright: ignore[reportAttributeAccessIssue]


class BlurEffect(EffectBase):
    def __init__(self, name="Blur"):
        super().__init__(
            name,
            params=[
                EffectParam("amount", float, 0.0, default=0.0),
                EffectParam("angle", float, 0.0, default=0.0),
                EffectParam("opacity", float, 1.0, default=1.0),
                EffectParam("blend_mode", str, "lighten_only", default="lighten_only"),
            ],
        )
        # OpenGL resources belong to the processing thread, not the GUI that
        # may construct an effect for its parameter editor.
        self.processor: BlurShaderProcessor | None = None

    def apply(self, input_data: Processable) -> Processable:
        img_rgb = np.array(input_data).astype(np.uint8)

        if self.get_parameter("amount") <= 0:
            return img_rgb

        if self.processor is None:
            self.processor = BlurShaderProcessor()
        blurred = self.processor.process(
            img_rgb,
            amount=self.get_parameter("amount"),
            angle=np.radians(self.get_parameter("angle")),
        ).astype(np.float32)

        base = add_alpha_channel(img_rgb).astype(np.float32)

        base /= 255.0
        blurred /= 255.0

        blend_func = getattr(bm, self.get_parameter("blend_mode"), bm.normal)
        blended = blend_func(base, blurred, self.get_parameter("opacity"))

        return (blended * 255).astype(np.uint8)
