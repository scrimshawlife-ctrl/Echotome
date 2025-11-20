from __future__ import annotations

import json
import struct
from typing import Optional

import numpy as np
from PIL import Image


# Steganography constants
STEGO_MARKER = b"ECHOTOME_V3"
STEGO_VERSION = "steg-1"
BITS_PER_CHANNEL = 2  # Use 2 LSBs per channel for capacity


def embed_payload_in_png(image: Image.Image, payload: dict) -> Image.Image:
    """
    Embed payload into PNG image using LSB steganography.

    Payload structure:
    {
        "rune_id": "ECH-...",
        "enc_mk": "base64...",  # Encrypted master key
        "roc_hash": "hex...",   # SHA-256 of ROC
        "riv": "hex...",        # Ritual Imprint Vector
        "version": "steg-1"
    }

    Encoding format:
    [MARKER (11 bytes)] [PAYLOAD_LEN (4 bytes)] [JSON_PAYLOAD (variable)]

    Args:
        image: PIL Image (RGB or RGBA mode)
        payload: Dictionary to embed

    Returns:
        New PIL Image with embedded payload

    Raises:
        ValueError: If image too small or payload too large
    """
    # Convert to RGB if needed
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    # Prepare payload
    payload_json = json.dumps(payload, sort_keys=True)
    payload_bytes = payload_json.encode("utf-8")

    # Build message: MARKER + LENGTH + PAYLOAD
    message = STEGO_MARKER + struct.pack(">I", len(payload_bytes)) + payload_bytes

    # Get image data
    img_array = np.array(image, dtype=np.uint8)
    height, width, channels = img_array.shape

    # Calculate capacity
    total_pixels = height * width
    capacity_bytes = (total_pixels * channels * BITS_PER_CHANNEL) // 8

    if len(message) > capacity_bytes:
        raise ValueError(
            f"Payload too large: {len(message)} bytes, capacity: {capacity_bytes} bytes"
        )

    # Embed message
    embedded = _embed_bytes(img_array, message, BITS_PER_CHANNEL)

    # Convert back to PIL Image
    return Image.fromarray(embedded, mode=image.mode)


def extract_payload_from_png(image: Image.Image) -> Optional[dict]:
    """
    Extract payload from PNG image with LSB steganography.

    Args:
        image: PIL Image with embedded payload

    Returns:
        Extracted payload dictionary, or None if no valid payload found

    Raises:
        ValueError: If payload corrupted or invalid
    """
    # Convert to RGB if needed
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    # Get image data
    img_array = np.array(image, dtype=np.uint8)

    # Extract marker
    marker = _extract_bytes(img_array, 0, len(STEGO_MARKER), BITS_PER_CHANNEL)

    if marker != STEGO_MARKER:
        return None  # No embedded payload

    # Extract payload length
    len_offset = len(STEGO_MARKER)
    len_bytes = _extract_bytes(img_array, len_offset, 4, BITS_PER_CHANNEL)
    payload_len = struct.unpack(">I", len_bytes)[0]

    # Sanity check payload length
    if payload_len > 1_000_000:  # 1 MB max
        raise ValueError(f"Invalid payload length: {payload_len}")

    # Extract payload
    payload_offset = len_offset + 4
    payload_bytes = _extract_bytes(img_array, payload_offset, payload_len, BITS_PER_CHANNEL)

    # Decode JSON
    try:
        payload_json = payload_bytes.decode("utf-8")
        payload = json.loads(payload_json)
        return payload
    except Exception as e:
        raise ValueError(f"Failed to decode payload: {e}")


def _embed_bytes(
    img_array: np.ndarray,
    message: bytes,
    bits_per_channel: int,
) -> np.ndarray:
    """
    Embed bytes into image array using LSB.

    Args:
        img_array: Image array (H, W, C)
        message: Bytes to embed
        bits_per_channel: Number of LSBs to use per channel

    Returns:
        Modified image array
    """
    # Create copy
    embedded = img_array.copy()

    height, width, channels = embedded.shape

    # Convert message to bits
    bits = _bytes_to_bits(message)

    # Embed bits
    bit_idx = 0
    for y in range(height):
        for x in range(width):
            for c in range(channels):
                if bit_idx >= len(bits):
                    return embedded

                # Clear LSBs and embed new bits
                pixel_val = embedded[y, x, c]
                mask = (0xFF << bits_per_channel) & 0xFF
                cleared = pixel_val & mask

                # Get bits to embed
                embed_bits = 0
                for b in range(bits_per_channel):
                    if bit_idx < len(bits):
                        embed_bits |= bits[bit_idx] << (bits_per_channel - 1 - b)
                        bit_idx += 1

                embedded[y, x, c] = cleared | embed_bits

    return embedded


def _extract_bytes(
    img_array: np.ndarray,
    byte_offset: int,
    num_bytes: int,
    bits_per_channel: int,
) -> bytes:
    """
    Extract bytes from image array using LSB.

    Args:
        img_array: Image array (H, W, C)
        byte_offset: Byte offset to start extraction
        num_bytes: Number of bytes to extract
        bits_per_channel: Number of LSBs per channel

    Returns:
        Extracted bytes
    """
    height, width, channels = img_array.shape

    # Calculate bit offset
    bit_offset = byte_offset * 8
    num_bits = num_bytes * 8

    # Extract bits
    bits = []
    bit_idx = 0

    for y in range(height):
        for x in range(width):
            for c in range(channels):
                if len(bits) >= num_bits:
                    break

                if bit_idx < bit_offset:
                    bit_idx += bits_per_channel
                    continue

                # Extract LSBs
                pixel_val = img_array[y, x, c]
                for b in range(bits_per_channel):
                    if len(bits) >= num_bits:
                        break
                    bit = (pixel_val >> (bits_per_channel - 1 - b)) & 1
                    bits.append(bit)

                bit_idx += bits_per_channel

            if len(bits) >= num_bits:
                break
        if len(bits) >= num_bits:
            break

    # Convert bits to bytes
    return _bits_to_bytes(bits[:num_bits])


def _bytes_to_bits(data: bytes) -> list[int]:
    """
    Convert bytes to list of bits.

    Args:
        data: Input bytes

    Returns:
        List of bits (0 or 1)
    """
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    """
    Convert list of bits to bytes.

    Args:
        bits: List of bits (0 or 1)

    Returns:
        Bytes
    """
    # Pad to multiple of 8
    while len(bits) % 8 != 0:
        bits.append(0)

    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        result.append(byte)

    return bytes(result)


def verify_stego_integrity(
    image: Image.Image,
    expected_rune_id: Optional[str] = None,
    expected_roc_hash: Optional[str] = None,
) -> bool:
    """
    Verify steganographic payload integrity.

    Args:
        image: PIL Image with embedded payload
        expected_rune_id: Optional expected rune ID
        expected_roc_hash: Optional expected ROC hash

    Returns:
        True if payload valid and matches expectations
    """
    try:
        payload = extract_payload_from_png(image)

        if payload is None:
            return False

        # Check required fields
        required = ["rune_id", "enc_mk", "roc_hash", "riv", "version"]
        if not all(k in payload for k in required):
            return False

        # Check version
        if payload["version"] != STEGO_VERSION:
            return False

        # Check expectations
        if expected_rune_id and payload["rune_id"] != expected_rune_id:
            return False

        if expected_roc_hash and payload["roc_hash"] != expected_roc_hash:
            return False

        return True

    except Exception:
        return False


def estimate_stego_capacity(image: Image.Image) -> int:
    """
    Estimate steganographic capacity of image.

    Args:
        image: PIL Image

    Returns:
        Capacity in bytes
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    width, height = image.size
    channels = len(image.getbands())

    total_pixels = width * height
    capacity_bytes = (total_pixels * channels * BITS_PER_CHANNEL) // 8

    # Subtract overhead
    overhead = len(STEGO_MARKER) + 4
    return max(0, capacity_bytes - overhead)


def get_stego_info(image: Image.Image) -> dict:
    """
    Get information about steganographic embedding.

    Args:
        image: PIL Image

    Returns:
        Dictionary with stego info
    """
    capacity = estimate_stego_capacity(image)
    payload = extract_payload_from_png(image)

    return {
        "has_payload": payload is not None,
        "capacity_bytes": capacity,
        "payload_size_bytes": len(json.dumps(payload).encode("utf-8")) if payload else 0,
        "payload": payload,
    }
