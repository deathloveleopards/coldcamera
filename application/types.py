
from typing import Union, Literal
from PIL import Image, ImageSequence
import numpy as np


""" Parameters literal types """

ParamType = Literal[
    "int_slider", "int_spinbox",
    "float_slider", "float_spinbox",
    "bool", "button", "enum", "string"
]

""" Processable images, arrays & sequences """

ImageLike = Union[Image.Image, np.ndarray]
SequenceLike = ImageSequence.Iterator
Processable = Union[ImageLike, SequenceLike]