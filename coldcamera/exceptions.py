class NotImplementedEffect(Exception):
    """Raised when an effect is not implemented."""

    def __init__(self, message="Current effect isn't implemented."):
        self.message = message
        super().__init__(self.message)


class InvalidValue(Exception):
    """Raised when an invalid value is provided."""

    def __init__(self, message="Invalid value provided."):
        self.message = message
        super().__init__(self.message)


class VideoOpenError(Exception):
    """Raised when a video cannot be opened."""

    def __init__(self, path: str):
        self.message = f"Cannot open video {path}"
        super().__init__(self.message)
