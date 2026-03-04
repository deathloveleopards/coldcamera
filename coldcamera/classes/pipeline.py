from typing import Any, Dict, Iterator, List, Optional, Union

from coldcamera.classes.effect import EffectBase
from coldcamera.effects.register import get_by_name
from coldcamera.types import ImageSequence, Processable


class ProcessingPipeline:
    """
    Manages a sequence (pipeline) of image processing effects.
    Supports both one-off processing (`apply_once`) and streaming (`apply_stream`).
    Includes caching for static inputs.

    :param effects: Optional initial list of EffectBase objects.
    """

    def __init__(self, effects: Optional[List[EffectBase]] = None):
        self.effects: List[EffectBase] = effects or []
        self._cache_input: Optional[Processable] = None
        self._cache_output: Optional[Processable] = None

    def _run_pipeline(self, frame: Processable) -> Processable:
        """
        Apply all enabled effects to a single frame.

        :param frame: Input frame.
        :return: Processed frame.
        """

        output = frame

        for eff in self.effects:
            if getattr(eff, "enabled", True):
                output = eff.apply(output)

        return output

    def apply_once(self, input_data: Processable) -> Processable:
        """
        Apply the pipeline to a single static image.
        Uses caching to avoid reprocessing if input is unchanged.

        :param input_data: Input frame.
        :return: Processed frame.
        """

        if input_data is self._cache_input:
            return self._cache_output  # pyright: ignore[reportReturnType]

        result = self._run_pipeline(input_data)

        self._cache_input = input_data
        self._cache_output = result

        return result

    def apply_stream(self, input_sequence: Union[Iterator[Processable], ImageSequence.Iterator]) -> Iterator[Processable]:
        """
        Generator: apply pipeline to each frame in a sequence.
        Suitable for GIF, MP4, or real-time sources (camera).

        :param input_sequence: Sequence or iterator of frames.
        :yield: Processed frames one by one.
        """

        for frame in input_sequence:
            if hasattr(frame, "copy"):
                frame = frame.copy()  # pyright: ignore[reportAttributeAccessIssue]
            yield self._run_pipeline(frame)

    def apply_frames(self, frames: List[Processable]) -> List[Processable]:
        """
        Apply pipeline to a list of frames.

        :param frames: List of frames.
        :return: List of processed frames.
        """

        return list(self.apply_stream(frames))  # pyright: ignore[reportArgumentType]

    def add_effect(self, effect: EffectBase) -> None:
        """
        Append effect to the end of the pipeline.

        :param effect: Effect to append to the pipeline.
        """

        self.effects.append(effect)

    def insert_effect(self, index: int, effect: EffectBase) -> None:
        """
        Insert effect at a specific index in the pipeline.

        :param index: Index where the effect should be inserted.
        :param effect: Effect to insert into the pipeline.
        """

        self.effects.insert(index, effect)

    def remove_effect(self, index: int) -> None:
        """
        Remove effect at a given index.

        :param index: Index of the effect to remove.
        """

        if 0 <= index < len(self.effects):
            del self.effects[index]

    def move_effect(self, old_index: int, new_index: int) -> None:
        """
        Reorder effects by moving one from old_index to new_index.

        :param old_index: Index of the effect to move.
        :param new_index: Index where the effect should be moved to.
        """

        if 0 <= old_index < len(self.effects):
            effect = self.effects.pop(old_index)
            self.effects.insert(new_index, effect)

    def to_dictionary(self) -> Dict[str, Any]:
        """
        Serialize the pipeline into a dictionary (preset format).
        Each effect is serialized via its `to_dict` method.

        :return: Dictionary with pipeline description.
        """

        return {"pipeline": [effect.to_dictionary() for effect in self.effects]}

    @classmethod
    def from_dictionary(cls, d: Dict[str, Any]) -> "ProcessingPipeline":
        """
        Deserialize pipeline from dictionary.

        :param d: Dictionary with serialized pipeline data.
        :return: ProcessingPipeline instance.
        :raise ValueError: If an unknown effect type is encountered.
        """

        effects: List[EffectBase] = []

        for eff_data in d.get("pipeline", []):
            eff_name = eff_data.get("type")
            effect_cls = get_by_name(eff_name)

            if effect_cls is None:
                raise ValueError(f"Unknown effect type: {eff_name}")

            effect = effect_cls.from_dictionary(eff_data)
            effects.append(effect)

        return cls(effects)

    def save_preset(self, path: str) -> None:
        """
        Save pipeline as JSON preset to a file.

        :param path: File path to save preset.
        """

        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dictionary(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load_preset(cls, path: str) -> "ProcessingPipeline":
        """
        Load pipeline from JSON preset file.

        :param path: Path to JSON preset file.
        :return: ProcessingPipeline instance.
        """

        import json

        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dictionary(d)
