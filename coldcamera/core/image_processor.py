from typing import Optional

import cv2
import numpy as np

from coldcamera.classes.pipeline import ProcessingPipeline


class ImageProcessor:
    """
    Service for processing image frames through the pipeline.

    Operates exclusively on NumPy arrays — no Qt dependency.
    QImage conversion is handled at the display boundary (window layer).
    """

    @staticmethod
    def ensure_uint8(arr: np.ndarray) -> np.ndarray:
        """
        Ensure the array is uint8, clipping values if necessary.

        :param arr: Input NumPy array.
        :return: Array with dtype uint8.
        """

        if arr.dtype != np.uint8:
            return np.clip(arr, 0, 255).astype(np.uint8)
        return arr

    @staticmethod
    def ensure_rgba(arr: np.ndarray) -> np.ndarray:
        """
        Ensure a frame has 4 channels (RGBA). Converts 3-channel RGB if needed.

        :param arr: Input NumPy frame.
        :return: RGBA NumPy frame.
        """

        if arr.ndim == 3 and arr.shape[2] == 3:
            return cv2.cvtColor(arr, cv2.COLOR_RGB2RGBA)
        return arr

    @classmethod
    def process_frame(cls, pipeline: ProcessingPipeline, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Apply the pipeline to a single NumPy frame.

        :param pipeline: ProcessingPipeline instance.
        :param frame: Input image as NumPy array (typically RGBA uint8).
        :return: Processed NumPy array, or None if input is None.
        """

        if frame is None:
            return None

        if len(pipeline.effects) == 0:
            return frame.copy()

        result = pipeline.apply_once(frame)
        return cls.ensure_uint8(result)
