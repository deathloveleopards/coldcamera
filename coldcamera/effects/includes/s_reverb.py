from pedalboard import Reverb
from pedalboard._pedalboard import Pedalboard

from coldcamera.classes.effect import EffectBase
from coldcamera.classes.layout import ParameterSlider
from coldcamera.classes.parameter import EffectParam
from coldcamera.types import Processable
from coldcamera.utils.sonarify_image import audio_bytes_to_image, image_to_audio_bytes

SAMPLE_RATE = 44100
NUM_CHANNELS = 1


class ReverbEffect(EffectBase):
    author: str = "serh11chyrva"

    def __init__(self, name="Reverb"):
        super().__init__(
            name,
            params=[EffectParam("room_size", float, 0.0, default=0.0)],
            layout_elements=[ParameterSlider("room_size", "Room Size", min_value=0.0, max_value=1.0, step=0.5)],
        )

    def apply(self, input_data: Processable) -> Processable:

        height, width, _ = input_data.shape  # pyright: ignore[reportAttributeAccessIssue]

        audio = image_to_audio_bytes(input_data)  # pyright: ignore[reportArgumentType]
        board = Pedalboard([Reverb(room_size=self.get_parameter("room_size"))])
        processed = board(audio, sample_rate=SAMPLE_RATE)

        result = audio_bytes_to_image(processed, width, height)

        return result
