
import numpy as np
import cv2


def add_alpha_channel(img_np):
    """Ensure RGBA format with alpha channel."""
    if img_np.ndim == 2:
        img_np = cv2.cvtColor(img_np.astype(np.uint8), cv2.COLOR_GRAY2RGB)
    if img_np.shape[2] == 3:
        alpha = np.full((img_np.shape[0], img_np.shape[1], 1), 255, dtype=img_np.dtype)
        img_np = np.concatenate((img_np, alpha), axis=2)
    return img_np