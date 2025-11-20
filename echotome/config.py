from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict


@dataclass
class EchotomeConfig:
    """
    Top-level configuration for an Echotome run.
    """

    input_audio: Path
    output_image: Path
    secret_key: str

    # Audio processing
    target_sample_rate: int = 16000
    frame_size: int = 1024
    hop_size: int = 256

    # Image / sigil properties
    image_width: int = 512
    image_height: int = 512
    contrast_boost: float = 1.5

    # Rune / hash options
    rune_prefix: str = "ECH"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["input_audio"] = str(self.input_audio)
        data["output_image"] = str(self.output_image)
        return data


@dataclass
class EchotomeResult:
    """
    Output metadata for an Echotome run.
    """

    rune_id: str
    checksum: str
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rune_id": self.rune_id,
            "checksum": self.checksum,
            "config": self.config,
        }
