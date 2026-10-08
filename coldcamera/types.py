"""
Type aliases for the coldcamera processing pipeline.

The canonical processing format is NumPy RGBA uint8 arrays.
QImage is only used at the viewport display boundary.
"""

from typing import TypeAlias

import numpy as np
from PIL import ImageSequence as ImageSequence  # noqa: F811 — re-export for external use

# The canonical data type for all image processing within the pipeline.
# All effects receive and return NumPy arrays (typically RGBA uint8).
Processable: TypeAlias = np.ndarray
