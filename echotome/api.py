"""
Echotome v3.2 REST API — Session & Locality Enforcement

Provides HTTP endpoints for:
- Vault management (create, list, delete)
- Encryption/decryption with AF-KDF
- Session management with time-limited access (ritual windows)
- Profile-based session TTLs (Quick: 1h, Ritual: 20m, Black: 5m)
- Privacy profiles with threat models
- Multi-track ritual support
- Locality enforcement (local-only operations, no telemetry)
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

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
from .privacy_profiles import list_profiles, profile_info, get_profile, describe_profile
from .audio_layer import extract_audio_features
from .crypto_core import derive_final_key, rune_id_from_key
from .sessions import (
    get_session_manager,
    Session,
    SessionConfig,
)
from .recovery import generate_recovery_codes, create_recovery_config


# Initialize FastAPI app
app = FastAPI(
    title="Echotome API",
    description="Ritual Cryptography Engine — Session & Locality Enforcement",
    version="3.2.0",
)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class SessionCreateRequest(BaseModel):
    vault_id: str
    profile: str
    ttl_seconds: Optional[int] = None


class SessionExtendRequest(BaseModel):
    additional_seconds: int


class SessionResponse(BaseModel):
    session_id: str
    vault_id: str
    profile: str
    created_at: float
    expires_at: float
    time_remaining: int
    time_remaining_formatted: str


class ProfileResponse(BaseModel):
    name: str
    kdf_time: int
    kdf_memory: int
    audio_weight: float
    deniable: bool
    threat_model_id: str
    threat_model_description: str
    default_session_ttl: int
    max_session_ttl: int
    recovery_enabled_default: bool


# ============================================================================
# Health & Info
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "3.1.0"}


@app.get("/info")
async def api_info():
    """API information and capabilities."""
    return {
        "name": "Echotome",
        "version": "3.2.0",
        "edition": "Session & Locality Enforcement",
        "features": [
            "session_management",
            "time_limited_sessions",
            "profile_based_ttls",
            "multi_track_rituals",
            "recovery_codes",
            "threat_models",
            "privacy_guardrails",
            "locality_enforcement",
        ],
        "locality": "All cryptographic operations performed locally",
    }


# ============================================================================
# Privacy Profiles (v3.1 Enhanced)
# ============================================================================

@app.get("/profiles")
async def get_profiles():
    """List all available privacy profiles with threat models and session TTLs (v3.2)."""
    profiles = list_profiles()
    return {
        "profiles": [
            {
                "name": p.name,
                "kdf_time": p.kdf_time,
                "kdf_memory": p.kdf_memory,
                "kdf_parallelism": getattr(p, "kdf_parallelism", 4),
                "audio_weight": p.audio_weight,
                "deniable": p.deniable,
                "requires_mic": getattr(p, "requires_mic", False),
                "requires_timing": getattr(p, "requires_timing", False),
                "hardware_recommended": getattr(p, "hardware_recommended", False),
                "threat_model_id": getattr(p, "threat_model_id", "unknown"),
                "threat_model_description": getattr(p, "threat_model_description", ""),
                "unrecoverable_default": getattr(p, "unrecoverable_default", False),
                # V3.2: Session management parameters
                "session_ttl_seconds": getattr(p, "session_ttl_seconds", 900),
                "session_ttl_formatted": f"{getattr(p, 'session_ttl_seconds', 900) // 60} minutes",
                "allow_plaintext_disk": getattr(p, "allow_plaintext_disk", True),
            }
            for p in profiles
        ],
        "info": profile_info(),
    }


@app.get("/profiles/{profile_name}")
async def get_profile_detail(profile_name: str):
    """Get detailed profile information including threat model."""
    try:
        description = describe_profile(profile_name)
        return description
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/profiles/{profile_name}/session_config")
async def get_profile_session_config(profile_name: str):
    """Get session configuration for a profile."""
    try:
        config = SessionConfig.for_profile(profile_name)
        return {
            "profile": profile_name,
            "default_ttl_seconds": config.default_ttl_seconds,
            "max_ttl_seconds": config.max_ttl_seconds,
            "auto_lock_on_background": config.auto_lock_on_background,
            "allow_external_apps": config.allow_external_apps,
            "secure_delete": config.secure_delete,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Session Management (v3.1)
# ============================================================================

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """
    Create a new ritual session (ritual window).

    Sessions provide time-limited access to decrypted vault content.
    Master keys are held in memory only during the session.
    """
    try:
        manager = get_session_manager()

        # Use profile-specific defaults if TTL not specified
        config = SessionConfig.for_profile(request.profile)
        ttl = request.ttl_seconds or config.default_ttl_seconds

        # Enforce max TTL
        if ttl > config.max_ttl_seconds:
            ttl = config.max_ttl_seconds

        # Create session (master_key would come from successful unlock)
        # For API, we create a placeholder - real key comes from decrypt flow
        session = manager.create_session(
            vault_id=request.vault_id,
            profile=request.profile,
            master_key=None,  # Set during actual unlock
            ttl_seconds=ttl,
        )

        return SessionResponse(
            session_id=session.session_id,
            vault_id=session.vault_id,
            profile=session.profile,
            created_at=session.created_at,
            expires_at=session.expires_at,
            time_remaining=session.time_remaining(),
            time_remaining_formatted=session.format_time_remaining(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    manager = get_session_manager()
    sessions = manager.list_sessions()

    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "vault_id": s.vault_id,
                "profile": s.profile,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "time_remaining": s.time_remaining(),
                "time_remaining_formatted": s.format_time_remaining(),
                "is_expired": s.is_expired(),
            }
            for s in sessions
        ],
        "count": len(sessions),
    }


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session by ID."""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {
        "session_id": session.session_id,
        "vault_id": session.vault_id,
        "profile": session.profile,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "time_remaining": session.time_remaining(),
        "time_remaining_formatted": session.format_time_remaining(),
        "last_activity": session.last_activity,
    }


@app.post("/sessions/{session_id}/extend")
async def extend_session(session_id: str, request: SessionExtendRequest):
    """Extend session TTL (within profile max limits)."""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        success = manager.extend_session(session_id, request.additional_seconds)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to extend session")

        # Get updated session
        session = manager.get_session(session_id)
        return {
            "session_id": session.session_id,
            "expires_at": session.expires_at,
            "time_remaining": session.time_remaining(),
            "time_remaining_formatted": session.format_time_remaining(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/sessions/{session_id}")
async def end_session(session_id: str, secure_delete: bool = True):
    """
    End session and securely cleanup all decrypted content.

    Args:
        session_id: Session to end
        secure_delete: Overwrite files with random data before deletion (default: True)
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    manager.end_session(session_id, secure_delete=secure_delete)

    return {
        "status": "ended",
        "session_id": session_id,
        "secure_delete": secure_delete,
    }


@app.post("/sessions/cleanup")
async def cleanup_expired_sessions():
    """Cleanup all expired sessions and their decrypted content."""
    manager = get_session_manager()
    count = manager.cleanup_expired_sessions()

    return {
        "status": "cleanup_complete",
        "sessions_cleaned": count,
    }


@app.delete("/sessions")
async def end_all_sessions(secure_delete: bool = True):
    """End all active sessions (emergency lock)."""
    manager = get_session_manager()
    count = manager.end_all_sessions(secure_delete=secure_delete)

    return {
        "status": "all_sessions_ended",
        "sessions_ended": count,
        "secure_delete": secure_delete,
    }


@app.get("/sessions/{session_id}/files")
async def list_session_files(session_id: str):
    """
    List all decrypted files in a session directory (v3.2).

    Returns file metadata for all files in the session's temporary directory.
    Files are automatically cleaned up when the session expires or is ended.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # List files in session temp directory
    files = []
    if session.session_dir.exists():
        for file_path in session.session_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "download_url": f"/sessions/{session_id}/files/{file_path.name}",
                })

    return {
        "session_id": session_id,
        "vault_id": session.vault_id,
        "profile": session.profile,
        "time_remaining": session.time_remaining(),
        "time_remaining_formatted": session.format_time_remaining(),
        "files": files,
        "file_count": len(files),
    }


@app.get("/sessions/{session_id}/files/{filename}")
async def download_session_file(session_id: str, filename: str):
    """
    Download a specific file from a session directory (v3.2).

    Files are only accessible within the session time window.
    Session must be active and not expired.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Construct file path (with basic path traversal protection)
    file_path = session.session_dir / filename

    # Security: Ensure file is within session directory
    try:
        file_path = file_path.resolve()
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not str(file_path).startswith(str(session.session_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found in session")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Update session activity
    session.last_activity = session.created_at  # Touch the session

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename,
    )


# ============================================================================
# Recovery Codes (v3.1)
# ============================================================================

@app.post("/recovery/generate")
async def generate_recovery(vault_id: str = Form(...), count: int = Form(5)):
    """
    Generate recovery codes for a vault.

    IMPORTANT: Codes are displayed ONCE. User must store them securely.
    Only hashes are stored in the vault configuration.
    """
    if count < 1 or count > 10:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10")

    codes = generate_recovery_codes(count=count)
    config = create_recovery_config(codes=codes, enabled=True, vault_id=vault_id)

    return {
        "vault_id": vault_id,
        "codes": codes,  # ONE-TIME DISPLAY
        "warning": "Store these codes securely. They will NOT be shown again.",
        "count": len(codes),
        "hashes_stored": len(config.hashed_codes),
    }


# ============================================================================
# Vault Management
# ============================================================================

@app.post("/create_vault")
async def api_create_vault(
    name: str = Form(...),
    profile: str = Form(...),
    audio_file: UploadFile = File(...),
    passphrase: str = Form(...),
    enable_recovery: bool = Form(True),
):
    """
    Create a new vault.

    Args:
        name: Vault name
        profile: Privacy profile (Quick Lock, Ritual Lock, Black Vault)
        audio_file: Audio file for AF-KDF
        passphrase: User passphrase
        enable_recovery: Enable recovery codes (default: True, except Black Vault)

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

        # Generate recovery codes if enabled
        recovery_codes = None
        if enable_recovery and not getattr(profile_obj, "unrecoverable_default", False):
            recovery_codes = generate_recovery_codes(count=5)

        # Clean up temp file
        tmp_path.unlink()

        response = {
            "vault_id": vault.id,
            "name": vault.name,
            "profile": vault.profile,
            "rune_id": vault.rune_id,
            "created_at": vault.created_at,
        }

        if recovery_codes:
            response["recovery_codes"] = recovery_codes
            response["recovery_warning"] = "Store these codes securely. They will NOT be shown again."

        return response

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
    create_session: bool = Form(True),
    vault_id: Optional[str] = Form(None),
):
    """
    Decrypt a file using Echotome AF-KDF.

    V3.2: Now creates time-limited sessions with profile-based TTLs.

    Args:
        audio_file: Audio file for AF-KDF (same as used for encryption)
        passphrase: User passphrase (same as used for encryption)
        encrypted_blob: JSON encrypted blob
        create_session: Create a ritual session for the decrypted content (default: True)
        vault_id: Optional vault ID to associate with session

    Returns:
        If create_session=True: Session metadata with file info
        If create_session=False: Direct file download (legacy mode)
    """
    try:
        # Parse encrypted blob to extract metadata
        blob_data = json.loads(encrypted_blob)
        profile = blob_data.get("profile", "Quick Lock")
        rune_id = blob_data.get("rune_id", "unknown")

        # Save uploaded audio to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_tmp:
            audio_tmp.write(await audio_file.read())
            audio_path = Path(audio_tmp.name)

        # Save encrypted blob to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".enc", mode="w") as blob_tmp:
            blob_tmp.write(encrypted_blob)
            blob_path = Path(blob_tmp.name)

        # Decrypt to temp location first
        with tempfile.NamedTemporaryFile(delete=False) as out_tmp:
            out_path = Path(out_tmp.name)

        # Extract audio features before decrypting (needed for session key)
        audio_features = extract_audio_features(audio_path)

        result = decrypt_with_echotome(
            audio_path,
            passphrase,
            blob_path,
            out_path,
        )

        # Clean up temp audio and blob
        audio_path.unlink()
        blob_path.unlink()

        if create_session:
            # V3.2: Create session with profile-based TTL
            manager = get_session_manager()

            # Derive master key for session storage
            profile_obj = get_profile(profile)
            master_key = derive_final_key(passphrase, audio_features, profile_obj)

            # Create session
            config = SessionConfig.for_profile(profile)
            session = manager.create_session(
                vault_id=vault_id or rune_id,
                profile=profile,
                master_key=master_key,
                ttl_seconds=config.default_ttl_seconds,
            )

            # Move decrypted file to session directory
            session_file_path = session.session_dir / "decrypted_file"
            shutil.move(str(out_path), str(session_file_path))

            # Return session metadata
            return {
                "status": "decrypted",
                "session_created": True,
                "session": {
                    "session_id": session.session_id,
                    "vault_id": session.vault_id,
                    "profile": session.profile,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                    "time_remaining_seconds": session.time_remaining(),
                    "time_remaining_formatted": session.format_time_remaining(),
                },
                "file": {
                    "filename": "decrypted_file",
                    "path": str(session_file_path),
                    "access_url": f"/sessions/{session.session_id}/files/decrypted_file",
                },
                "rune_id": result.get("rune_id"),
                "profile": result.get("profile"),
            }
        else:
            # Legacy mode: return file directly
            response = FileResponse(
                out_path,
                media_type="application/octet-stream",
                filename="decrypted_file",
            )
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

    # Check for active session
    manager = get_session_manager()
    session = manager.get_session_by_vault(vault_id)

    response = {
        "id": vault.id,
        "name": vault.name,
        "profile": vault.profile,
        "rune_id": vault.rune_id,
        "created_at": vault.created_at,
        "updated_at": vault.updated_at,
        "file_count": vault.file_count,
        "has_active_session": session is not None,
    }

    if session:
        response["session"] = {
            "session_id": session.session_id,
            "time_remaining": session.time_remaining(),
            "time_remaining_formatted": session.format_time_remaining(),
        }

    return response


@app.delete("/vaults/{vault_id}")
async def api_delete_vault(vault_id: str):
    """Delete a vault."""
    # End any active session first
    manager = get_session_manager()
    session = manager.get_session_by_vault(vault_id)
    if session:
        manager.end_session(session.session_id, secure_delete=True)

    success = delete_vault(vault_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vault not found")

    return {"status": "deleted", "vault_id": vault_id}


# ============================================================================
# Server
# ============================================================================

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
