from pedalboard import LowpassFilter
from pedalboard._pedalboard import Pedalboard

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.layout import ParameterSlider
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable
from coldcamera.utils.sonarify_image import audio_bytes_to_image, image_to_audio_bytes

SAMPLE_RATE = 44100
NUM_CHANNELS = 1


class LowPassEffect(EffectBase):
    author: str = "serh11chyrva"

    def __init__(self, name="Low Pass Filter"):
        super().__init__(
            name,
            params=[EffectParam("cutoff_frequency_hz", float, 2000.0, default=2000.0)],
            layout_elements=[ParameterSlider("cutoff_frequency_hz", "Cutoff Frequency", min_value=10.0, max_value=20000.0, step=1.0)],
        )

    def apply(self, input_data: Processable) -> Processable:

        height, width, _ = input_data.shape  # pyright: ignore[reportAttributeAccessIssue]

        audio = image_to_audio_bytes(input_data)  # pyright: ignore[reportArgumentType]
        board = Pedalboard([LowpassFilter(cutoff_frequency_hz=self.get_parameter("cutoff_frequency_hz"))])
        processed = board(audio, sample_rate=SAMPLE_RATE)

        result = audio_bytes_to_image(processed, width, height)

        return result
