import cv2
import numpy as np

from coldcamera.exceptions import VideoOpenError


class VideoFrameProvider:
    """
    Provides access to video frames from a file.

    :param path: Path to the video file.
    :raise VideoOpenError: If the video cannot be opened.
    """

    def __init__(self, path: str):
        """
        Initialize the video frame provider.

        :param path: Path to the video file.
        :raise VideoOpenError: If the video cannot be opened.
        """

        self.cap = cv2.VideoCapture(path)

        if not self.cap.isOpened():
            raise VideoOpenError(path=path)

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25

    def get_frame(self, index: int) -> np.ndarray | None:
        """
        Retrieve a specific frame from the video.

        :param index: Frame index to retrieve.
        :return: Frame as an RGBA numpy array, or None if index is invalid or frame cannot be read.
        """

        if index < 0 or index >= self.frame_count:
            return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)

        ret, frame = self.cap.read()

        if not ret:
            return None

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

    def release(self):
        """Release the video capture resources."""

        self.cap.release()
