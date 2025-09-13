
from typing import Optional, List, Dict, Any, Iterator, Union

from application.classes.register import EFFECT_REGISTRY
from application.classes.effect import EffectBase
from application.types import Processable, ImageSequence


class ProcessingPipeline:
    """
    Manages a sequence (pipeline) of image processing effects.
    Supports both one-off processing (apply_once) and streaming (apply_stream).
    Includes caching for static inputs.

    :param effects: Optional initial list of EffectBase objects.
    """

    def __init__(self, effects: Optional[List["EffectBase"]] = None):
        self.effects: List["EffectBase"] = effects or []

        self._cache_input = None
        self._cache_output = None

    def _run_pipeline(self, frame: Processable) -> Processable:
        """Apply all effects to a single frame."""
        output = frame
        for eff in self.effects:
            output = eff.apply(output)
        return output

    def apply_once(self, input_data: Processable) -> Processable:
        """
        Apply pipeline to a single static image.
        Uses caching to avoid reprocessing if input is unchanged.
        """
        if input_data is self._cache_input:
            return self._cache_output

        result = self._run_pipeline(input_data)
        self._cache_input = input_data
        self._cache_output = result
        return result

    def apply_stream(self, input_sequence: Union[Iterator[Processable], ImageSequence.Iterator]) -> Iterator[
        Processable]:
        """
        Generator: apply pipeline to each frame in a sequence.
        Suitable for GIF, MP4, or real-time sources (camera).
        """
        for frame in input_sequence:
            if hasattr(frame, "copy"):
                frame = frame.copy()
            yield self._run_pipeline(frame)

    def add_effect(self, effect: "EffectBase") -> None:
        """Append effect to the end of the pipeline."""
        self.effects.append(effect)

    def insert_effect(self, index: int, effect: "EffectBase") -> None:
        """Insert effect at a specific index in the pipeline."""
        self.effects.insert(index, effect)

    def remove_effect(self, index: int) -> None:
        """Remove effect at given index."""
        if 0 <= index < len(self.effects):
            del self.effects[index]

    def move_effect(self, old_index: int, new_index: int) -> None:
        """Reorder effects by moving one from old_index to new_index."""
        if 0 <= old_index < len(self.effects):
            effect = self.effects.pop(old_index)
            self.effects.insert(new_index, effect)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the pipeline into a dictionary (preset format).
        Each effect is serialized via its `to_dict` method.

        :return: Dict with pipeline description.
        """
        return {
            "pipeline": [effect.to_dict() for effect in self.effects]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessingPipeline":
        """
        Deserialize pipeline from dictionary.

        :param d: Dict with serialized pipeline data.
        :return: ProcessingPipeline instance.
        """
        effects: List["EffectBase"] = []
        for eff_data in d.get("pipeline", []):
            eff_type = eff_data.get("type")
            if eff_type not in EFFECT_REGISTRY:
                raise ValueError(f"Unknown effect type: {eff_type}")
            effect_cls = EFFECT_REGISTRY[eff_type]
            effect = effect_cls.from_dict(eff_data)
            effects.append(effect)
        return cls(effects)

    def save_preset(self, path: str) -> None:
        """Save pipeline as JSON preset to file."""
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load_preset(cls, path: str) -> "ProcessingPipeline":
        """Load pipeline from JSON preset file."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)