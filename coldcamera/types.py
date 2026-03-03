
from typing import Union

from PIL import Image, ImageSequence
from numpy import ndarray


""" Processable images, arrays & sequences """

ImageLike = Union[Image.Image, ndarray]
SequenceLike = ImageSequence.Iterator
Processable = Union[ImageLike, SequenceLike]