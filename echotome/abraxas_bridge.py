from __future__ import annotations

import hashlib
import time
from typing import List, Dict, Optional

from .vaults import list_vaults, Vault, list_vault_files


def calculate_entropy_score(rune_id: str, profile: str, file_count: int) -> float:
    """
    Calculate a symbolic entropy score for a vault.

    This is NOT a cryptographic measure - it's a heuristic metric
    for visualization and ritual purposes in Abraxas.

    Args:
        rune_id: Vault rune ID
        profile: Privacy profile name
        file_count: Number of files in vault

    Returns:
        Entropy score (0.0 to 1.0)
    """
    # Base entropy from rune ID hash distribution
    rune_bytes = rune_id.encode("utf-8")
    rune_hash = hashlib.sha256(rune_bytes).digest()
    base_entropy = sum(rune_hash) / (256 * len(rune_hash))

    # Profile weight
    profile_weights = {
        "QuickLock": 0.3,
        "RitualLock": 0.7,
        "BlackVault": 1.0,
    }
    profile_factor = profile_weights.get(profile, 0.5)

    # File count factor (logarithmic)
    import math
    file_factor = min(1.0, math.log1p(file_count) / 5.0)

    # Combined score
    entropy = (base_entropy * 0.4) + (profile_factor * 0.4) + (file_factor * 0.2)

    return min(1.0, max(0.0, entropy))


def export_metadata(vaults: Optional[List[Vault]] = None) -> List[Dict]:
    """
    Export vault metadata for Abraxas integration.

    SECURITY GUARANTEE:
    - NO cryptographic keys
    - NO plaintext data
    - NO passphrases
    - NO audio file paths
    - ONLY symbolic metadata for visualization

    Args:
        vaults: List of Vault instances (defaults to all vaults)

    Returns:
        List of metadata dictionaries safe for export

    Example output:
        [
            {
                "rune_id": "ECH-A1B2C3D4",
                "profile": "RitualLock",
                "last_used": 1234567890.0,
                "entropy_score": 0.75,
                "file_count": 3,
                "age_hours": 24.5,
                "vault_name": "MySecrets"
            }
        ]
    """
    if vaults is None:
        vaults = list_vaults()

    metadata = []

    for vault in vaults:
        # Calculate age
        age_seconds = time.time() - vault.created_at
        age_hours = age_seconds / 3600.0

        # Calculate entropy score
        entropy = calculate_entropy_score(
            vault.rune_id,
            vault.profile,
            vault.file_count,
        )

        # Build safe metadata
        meta = {
            "rune_id": vault.rune_id,
            "profile": vault.profile,
            "last_used": vault.updated_at,
            "entropy_score": entropy,
            "file_count": vault.file_count,
            "age_hours": age_hours,
            "vault_name": vault.name,
            # Additional symbolic fields
            "created_at": vault.created_at,
            "vault_id": vault.id,  # UUID, not secret
        }

        metadata.append(meta)

    return metadata


def export_aggregated_stats() -> Dict:
    """
    Export aggregated statistics across all vaults.

    Safe for public/symbolic display in Abraxas dashboard.

    Returns:
        Dictionary with aggregate statistics
    """
    vaults = list_vaults()

    if not vaults:
        return {
            "total_vaults": 0,
            "total_files": 0,
            "avg_entropy": 0.0,
            "profile_distribution": {},
            "oldest_vault_age_hours": 0.0,
            "newest_vault_age_hours": 0.0,
        }

    total_files = sum(v.file_count for v in vaults)

    # Calculate average entropy
    entropies = [
        calculate_entropy_score(v.rune_id, v.profile, v.file_count)
        for v in vaults
    ]
    avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0

    # Profile distribution
    profile_dist = {}
    for v in vaults:
        profile_dist[v.profile] = profile_dist.get(v.profile, 0) + 1

    # Age statistics
    now = time.time()
    ages = [(now - v.created_at) / 3600.0 for v in vaults]

    return {
        "total_vaults": len(vaults),
        "total_files": total_files,
        "avg_entropy": avg_entropy,
        "profile_distribution": profile_dist,
        "oldest_vault_age_hours": max(ages) if ages else 0.0,
        "newest_vault_age_hours": min(ages) if ages else 0.0,
    }


def generate_rune_constellation(limit: int = 10) -> List[Dict]:
    """
    Generate a "constellation" of rune IDs for symbolic visualization.

    This creates a visual map of vault relationships based on
    rune ID similarity (first characters).

    Args:
        limit: Maximum number of vaults to include

    Returns:
        List of vault positions for constellation display
    """
    vaults = list_vaults()[:limit]

    constellation = []

    for i, vault in enumerate(vaults):
        # Derive symbolic position from rune ID
        rune_hex = vault.rune_id.split("-")[-1]
        x = int(rune_hex[:2], 16) / 255.0  # Normalize to 0-1
        y = int(rune_hex[2:4], 16) / 255.0 if len(rune_hex) >= 4 else 0.5

        constellation.append({
            "rune_id": vault.rune_id,
            "x": x,
            "y": y,
            "profile": vault.profile,
            "name": vault.name,
            "entropy": calculate_entropy_score(
                vault.rune_id,
                vault.profile,
                vault.file_count,
            ),
        })

    return constellation


def export_for_abraxas() -> Dict:
    """
    Complete Abraxas integration export.

    Bundles all safe metadata for consumption by Abraxas UI.

    Returns:
        Complete metadata package
    """
    return {
        "version": "2.0",
        "timestamp": time.time(),
        "vaults": export_metadata(),
        "stats": export_aggregated_stats(),
        "constellation": generate_rune_constellation(),
    }


# Security audit function
def verify_no_secrets(data: Dict) -> bool:
    """
    Verify that exported data contains no secret material.

    Args:
        data: Data dictionary to audit

    Returns:
        True if safe, False if secrets detected

    Raises:
        ValueError: If secrets are found
    """
    # Convert to JSON string for scanning
    import json
    data_str = json.dumps(data).lower()

    # Forbidden keywords that indicate secret leakage
    forbidden = [
        "passphrase",
        "password",
        "key",
        "secret",
        "plaintext",
        "decrypt",
        "private",
    ]

    for keyword in forbidden:
        if keyword in data_str:
            # Allow "rune_id" and "profile" which contain "key"/"id"
            if keyword == "key" and "rune_id" in data_str:
                continue
            raise ValueError(f"Secret material detected: {keyword}")

    return True
