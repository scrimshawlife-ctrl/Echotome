from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from .pipeline import encrypt_with_echotome, decrypt_with_echotome
from .vaults import (
    create_vault,
    list_vaults,
    get_vault,
    delete_vault,
    encrypt_file_to_vault,
    decrypt_file_from_vault,
    get_vault_stats,
)
from .privacy_profiles import list_profiles, profile_info
from .audio_layer import extract_audio_features
from .crypto_core import derive_final_key, rune_id_from_key
from .privacy_profiles import get_profile


# Initialize FastAPI app
app = FastAPI(
    title="Echotome API",
    description="Audio-Field Key Derivation and Crypto-Sigil Engine",
    version="2.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/profiles")
async def get_profiles():
    """List all available privacy profiles."""
    profiles = list_profiles()
    return {
        "profiles": [
            {
                "name": p.name,
                "kdf_time": p.kdf_time,
                "kdf_memory": p.kdf_memory,
                "audio_weight": p.audio_weight,
                "deniable": p.deniable,
            }
            for p in profiles
        ],
        "info": profile_info(),
    }


@app.post("/create_vault")
async def api_create_vault(
    name: str = Form(...),
    profile: str = Form(...),
    audio_file: UploadFile = File(...),
    passphrase: str = Form(...),
):
    """
    Create a new vault.

    Args:
        name: Vault name
        profile: Privacy profile (QuickLock, RitualLock, BlackVault)
        audio_file: Audio file for AF-KDF
        passphrase: User passphrase

    Returns:
        Vault metadata with rune_id
    """
    try:
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio_file.read())
            tmp_path = Path(tmp.name)

        # Extract features and derive key
        audio_features = extract_audio_features(tmp_path)
        profile_obj = get_profile(profile)
        key = derive_final_key(passphrase, audio_features, profile_obj)
        rune_id = rune_id_from_key(key)

        # Create vault
        vault = create_vault(name, profile, rune_id)

        # Clean up temp file
        tmp_path.unlink()

        return {
            "vault_id": vault.id,
            "name": vault.name,
            "profile": vault.profile,
            "rune_id": vault.rune_id,
            "created_at": vault.created_at,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/encrypt")
async def api_encrypt(
    audio_file: UploadFile = File(...),
    passphrase: str = Form(...),
    profile: str = Form(...),
    data_file: UploadFile = File(...),
):
    """
    Encrypt a file using Echotome AF-KDF.

    Args:
        audio_file: Audio file for AF-KDF
        passphrase: User passphrase
        profile: Privacy profile
        data_file: File to encrypt

    Returns:
        Encrypted blob metadata
    """
    try:
        # Save uploaded files to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_tmp:
            audio_tmp.write(await audio_file.read())
            audio_path = Path(audio_tmp.name)

        with tempfile.NamedTemporaryFile(delete=False) as data_tmp:
            data_tmp.write(await data_file.read())
            data_path = Path(data_tmp.name)

        # Encrypt
        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as out_tmp:
            out_path = Path(out_tmp.name)

        result = encrypt_with_echotome(
            audio_path,
            passphrase,
            profile,
            data_path,
            out_path,
        )

        # Read encrypted blob
        with open(out_path, "r") as f:
            encrypted_blob = f.read()

        # Clean up
        audio_path.unlink()
        data_path.unlink()
        out_path.unlink()

        return {
            "rune_id": result["rune_id"],
            "profile": result["profile"],
            "encrypted_blob": encrypted_blob,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/decrypt")
async def api_decrypt(
    audio_file: UploadFile = File(...),
    passphrase: str = Form(...),
    encrypted_blob: str = Form(...),
):
    """
    Decrypt a file using Echotome AF-KDF.

    Args:
        audio_file: Audio file for AF-KDF (same as used for encryption)
        passphrase: User passphrase (same as used for encryption)
        encrypted_blob: JSON encrypted blob

    Returns:
        Decrypted file
    """
    try:
        # Save uploaded audio to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_tmp:
            audio_tmp.write(await audio_file.read())
            audio_path = Path(audio_tmp.name)

        # Save encrypted blob to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc", mode="w") as blob_tmp:
            blob_tmp.write(encrypted_blob)
            blob_path = Path(blob_tmp.name)

        # Decrypt
        with tempfile.NamedTemporaryFile(delete=False) as out_tmp:
            out_path = Path(out_tmp.name)

        result = decrypt_with_echotome(
            audio_path,
            passphrase,
            blob_path,
            out_path,
        )

        # Return decrypted file
        response = FileResponse(
            out_path,
            media_type="application/octet-stream",
            filename="decrypted_file",
        )

        # Clean up will happen after response is sent
        # Note: This is simplified; production code should use background tasks

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/vaults")
async def api_list_vaults():
    """List all vaults."""
    vaults = list_vaults()
    return {
        "vaults": [
            {
                "id": v.id,
                "name": v.name,
                "profile": v.profile,
                "rune_id": v.rune_id,
                "created_at": v.created_at,
                "updated_at": v.updated_at,
                "file_count": v.file_count,
            }
            for v in vaults
        ],
        "stats": get_vault_stats(),
    }


@app.get("/vaults/{vault_id}")
async def api_get_vault(vault_id: str):
    """Get vault by ID."""
    vault = get_vault(vault_id)
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    return {
        "id": vault.id,
        "name": vault.name,
        "profile": vault.profile,
        "rune_id": vault.rune_id,
        "created_at": vault.created_at,
        "updated_at": vault.updated_at,
        "file_count": vault.file_count,
    }


@app.delete("/vaults/{vault_id}")
async def api_delete_vault(vault_id: str):
    """Delete a vault."""
    success = delete_vault(vault_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vault not found")

    return {"status": "deleted", "vault_id": vault_id}


# Run the API server
def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the Echotome API server.

    Args:
        host: Host address
        port: Port number
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
