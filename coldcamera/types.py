from typing import TypeAlias, Union

from numpy import ndarray
from PIL import Image, ImageSequence

ImageLike: TypeAlias = Union[Image.Image, ndarray]
SequenceLike: TypeAlias = ImageSequence.Iterator
Processable: TypeAlias = Union[ImageLike, SequenceLike]
