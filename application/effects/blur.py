
import numpy as np
import blend_modes as bm

from application.classes.effect import EffectBase
from application.classes.parameter import EffectParam
from application.classes.layout import ParameterSlider, ParameterDropdown
from application.classes.shader_processor import ShaderProcessorBase
from application.utils.add_alpha_channel import add_alpha_channel
from application.enums import BlendModeType
from application.types import Processable


class BlurShaderProcessor(ShaderProcessorBase):
    def fragment_shader(self) -> str:
        return '''
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
        '''

    def set_uniforms(self, **kwargs):
        self.prog['amount'].value = float(kwargs.get('amount', 0.0))
        self.prog['angle'].value = float(kwargs.get('angle', 0.0))


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
            layout_elements=[
                ParameterSlider("amount", "Blur amount", min_value=0, max_value=100, step=1),
                ParameterSlider("angle", "Blur angle", min_value=-180, max_value=180, step=1),
                ParameterSlider("opacity", "Opacity", min_value=0, max_value=1, step=0.05),
                ParameterDropdown("blend_mode", "Blend mode", enum_type=BlendModeType,
                                  default=BlendModeType.NORMAL,
                                  value=BlendModeType.NORMAL),
            ],
        )
        self.processor = BlurShaderProcessor()

    def apply(self, input_data: Processable) -> Processable:
        img_rgb = np.array(input_data).astype(np.uint8)

        if self.get_param("amount") <= 0:
            return img_rgb

        blurred = self.processor.process(
            img_rgb,
            amount=self.get_param("amount"),
            angle=np.radians(self.get_param("angle")),
        ).astype(np.float32)

        base = add_alpha_channel(img_rgb).astype(np.float32)

        base /= 255.0
        blurred /= 255.0

        blend_func = getattr(bm, self.get_param("blend_mode"), bm.normal)
        blended = blend_func(base, blurred, self.get_param("opacity"))

        return (blended * 255).astype(np.uint8)
