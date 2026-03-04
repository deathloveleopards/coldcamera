from pedalboard import Phaser
from pedalboard._pedalboard import Pedalboard

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.layout import ParameterSlider
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable
from coldcamera.utils.sonarify_image import audio_bytes_to_image, image_to_audio_bytes

SAMPLE_RATE = 44100
NUM_CHANNELS = 1


class PhaserEffect(EffectBase):
    author: str = "serh11chyrva"

    def __init__(self, name="Phaser"):
        super().__init__(
            name,
            params=[
                EffectParam("rate", float, 1.5, default=1.5),
                EffectParam("depth", float, 0.7, default=0.7),
            ],
            layout_elements=[
                ParameterSlider("rate", "Rate", min_value=0.0, max_value=10.0, step=0.1),
                ParameterSlider("depth", "Depth", min_value=0.0, max_value=1.0, step=0.1),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:

        height, width, _ = input_data.shape  # pyright: ignore[reportAttributeAccessIssue]

        audio = image_to_audio_bytes(input_data)  # pyright: ignore[reportArgumentType]
        board = Pedalboard([Phaser(rate_hz=self.get_parameter("rate"), depth=self.get_parameter("depth"))])
        processed = board(audio, sample_rate=SAMPLE_RATE)

        result = audio_bytes_to_image(processed, width, height)

        return result
