"""Immutable serialized pipeline snapshots for cross-thread work."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from coldcamera.classes.pipeline import ProcessingPipeline


@dataclass(frozen=True)
class PipelineSnapshot:
    """A detached pipeline payload that can safely cross worker boundaries."""

    payload: str

    @classmethod
    def from_pipeline(cls, pipeline: ProcessingPipeline) -> "PipelineSnapshot":
        data = pipeline.to_dictionary()
        for effect_data, effect in zip(data["pipeline"], pipeline.effects):
            effect_data["enabled"] = bool(effect.enabled)
        return cls(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    @classmethod
    def from_dictionary(cls, data: Mapping[str, Any]) -> "PipelineSnapshot":
        return cls(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    def to_dictionary(self) -> dict[str, Any]:
        return json.loads(self.payload)

    def build_pipeline(self) -> ProcessingPipeline:
        data = self.to_dictionary()
        pipeline = ProcessingPipeline.from_dictionary(data)
        for effect, effect_data in zip(pipeline.effects, data.get("pipeline", [])):
            effect.enabled = bool(effect_data.get("enabled", True))
        return pipeline
