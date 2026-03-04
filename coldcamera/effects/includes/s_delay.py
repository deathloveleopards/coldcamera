from pedalboard import Delay
from pedalboard._pedalboard import Pedalboard

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.layout import ParameterSlider
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable
from coldcamera.utils.sonarify_image import audio_bytes_to_image, image_to_audio_bytes

SAMPLE_RATE = 44100
NUM_CHANNELS = 1


class DelayEffect(EffectBase):
    author: str = "serh11chyrva"

    def __init__(self, name="Delay"):
        super().__init__(
            name,
            params=[
                EffectParam("delay_seconds", float, 0.1, default=0.1),
                EffectParam("feedback", float, 0.4, default=0.4),
                EffectParam("mix", float, 0.5, default=0.5),
            ],
            layout_elements=[
                ParameterSlider("delay_seconds", "Delay (s)", min_value=0.0, max_value=30.0, step=0.1),
                ParameterSlider("feedback", "Feedback", min_value=0.0, max_value=1.0, step=0.05),
                ParameterSlider("mix", "Mix", min_value=0.0, max_value=1.0, step=0.05),
            ],
        )

    def apply(self, input_data: Processable) -> Processable:

        height, width, _ = input_data.shape  # pyright: ignore[reportAttributeAccessIssue]

        audio = image_to_audio_bytes(input_data)  # pyright: ignore[reportArgumentType]
        board = Pedalboard(
            [
                Delay(delay_seconds=self.get_parameter("delay_seconds"), feedback=self.get_parameter("feedback"), mix=self.get_parameter("mix")),
            ]
        )
        processed = board(audio, sample_rate=SAMPLE_RATE)

        result = audio_bytes_to_image(processed, width, height)

        return result
