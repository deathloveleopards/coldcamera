
from enum import Enum


class NoiseType(Enum):
    GAUSSIAN = ("gaussian", "Gaussian")
    SALT = ("salt", "Salt")
    PEPPER = ("pepper", "Pepper")
    SPECKLE = ("speckle", "Speckle")

    def __str__(self):
        return self.value[1]

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]


class ChromaticAberrationType(Enum):
    RED_BLUE = ("rb", "Red + Blue")
    RED_GREEN = ("rg", "Red + Green")
    GREEN_BLUE = ("gb", "Green + Blue")
    def __str__(self):
        return self.value[1]

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]


class RescaleResolution(Enum):
    R128x96 = ("128x96", "128 x 96 (QCIF)")
    R160x120 = ("160x120", "160 x 120 (QQVGA)")
    R176x144 = ("176x144", "176 x 144 (QCIF)")
    R240x160 = ("240x160", "240 x 160 (HQVGA)")

    R320x240 = ("320x240", "320 x 240 (QVGA)")
    R352x288 = ("352x288", "352 x 288 (CIF)")
    R400x240 = ("400x240", "400 x 240 (WQVGA)")
    R480x320 = ("480x320", "480 x 320 (HVGA)")

    R640x480 = ("640x480", "640 x 480 (VGA)")
    R720x480 = ("720x480", "720 x 480 (NTSC)")
    R800x480 = ("800x480", "800 x 480 (WVGA)")
    R800x600 = ("800x600", "800 x 600 (SVGA)")

    R960x640 = ("960x640", "960 x 640")
    R1024x600 = ("1024x600", "1024 x 600 (WSVGA)")
    R1024x768 = ("1024x768", "1024 x 768 (XGA)")
    R1152x864 = ("1152x864", "1152 x 864")

    R1280x720 = ("1280x720", "1280 x 720 (HD)")
    R1280x960 = ("1280x960", "1280 x 960")
    R1280x1024 = ("1280x1024", "1280 x 1024 (SXGA)")

    R1400x1050 = ("1400x1050", "1400 x 1050 (SXGA+)")
    R1600x1200 = ("1600x1200", "1600 x 1200 (UXGA)")

    R1920x1080 = ("1920x1080", "1920 x 1080 (Full HD)")
    R2048x1536 = ("2048x1536", "2048 x 1536 (QXGA)")
    R2560x1920 = ("2560x1920", "2560 x 1920 (5 MP)")

    def __str__(self):
        return self.value[1]

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]


class BlendModeType(Enum):
    SOFT_LIGHT = ("soft_light", "Soft Light")
    LIGHTEN_ONLY = ("lighten_only", "Lighten Only")
    DODGE = ("dodge", "Dodge")
    ADDITION = ("addition", "Addition")
    DARKEN_ONLY = ("darken_only", "Darken Only")
    MULTIPLY = ("multiply", "Multiply")
    HARD_LIGHT = ("hard_light", "Hard Light")
    DIFFERENCE = ("difference", "Difference")
    SUBTRACT = ("subtract", "Subtract")
    GRAIN_EXTRACT = ("grain_extract", "Grain Extract")
    GRAIN_MERGE = ("grain_merge", "Grain Merge")
    DIVIDE = ("divide", "Divide")
    OVERLAY = ("overlay", "Overlay")
    NORMAL = ("normal", "Normal")

    def __str__(self):
        return self.value[1]

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]
