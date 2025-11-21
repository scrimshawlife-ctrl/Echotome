from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import EchotomeConfig
from .pipeline import run_echotome


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Echotome — audio → crypto-sigil engine",
    )
    parser.add_argument(
        "input_audio",
        type=str,
        help="Path to input audio file (wav, flac, ogg, etc. as supported by soundfile).",
    )
    parser.add_argument(
        "output_image",
        type=str,
        help="Path to output PNG image.",
    )
    parser.add_argument(
        "--key",
        type=str,
        required=True,
        help="Secret key / passphrase for deterministic sigil generation.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=512,
        help="Output image width (default: 512).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=512,
        help="Output image height (default: 512).",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.5,
        help="Contrast boost factor (default: 1.5).",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Optional path to write JSON metadata (rune_id, checksum, config).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = EchotomeConfig(
        input_audio=Path(args.input_audio),
        output_image=Path(args.output_image),
        secret_key=args.key,
        image_width=args.width,
        image_height=args.height,
        contrast_boost=args.contrast,
    )

    result = run_echotome(config)

    print(f"[Echotome] Rune ID: {result.rune_id}")
    print(f"[Echotome] Checksum: {result.checksum}")
    print(f"[Echotome] Image written to: {config.output_image}")

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"[Echotome] Metadata JSON written to: {json_path}")


if __name__ == "__main__":
    main()
