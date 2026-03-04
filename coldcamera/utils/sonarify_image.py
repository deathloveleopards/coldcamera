import numpy as np


def image_to_audio_bytes(image: np.ndarray) -> np.ndarray:
    """
    Convert image array (H,W,3 uint8) into pedalboard-compatible audio buffer.

    :param image: uint8 array with shape (height, width, 3):
    :return: float32 array with shape (1, samples)
    """

    if image.shape[2] == 4:
        image = image[:, :, :3]

    byte_data = image.tobytes()

    audio = np.frombuffer(byte_data, dtype=np.uint8).astype(np.float32)

    # 0..255 -> -1..1
    audio = (audio / 127.5) - 1.0

    # pedalboard expects (channels, samples)
    audio = np.expand_dims(audio, axis=0)

    return audio


def audio_bytes_to_image(audio: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Convert pedalboard audio buffer back into image.

    :param audio: pedalboard audio buffer with shape (channels, samples)
    :param width: image width
    :param height: image height
    :return: uint8 array with shape (height, width, 4)
    """

    audio = np.clip(audio, -1.0, 1.0)

    processed_bytes = ((audio[0] + 1.0) * 127.5).astype(np.uint8)

    expected_size = width * height * 3

    if processed_bytes.size < expected_size:
        processed_bytes = np.pad(processed_bytes, (0, expected_size - processed_bytes.size), mode="constant")
    elif processed_bytes.size > expected_size:
        processed_bytes = processed_bytes[:expected_size]

    rgb = processed_bytes.reshape((height, width, 3))

    alpha = np.full((height, width, 1), 255, dtype=np.uint8)

    return np.concatenate((rgb, alpha), axis=2)
