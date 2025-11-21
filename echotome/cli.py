"""
Echotome v3.1 CLI

Commands:
- sigil: Generate crypto-sigil from audio (legacy v0.2.0)
- encrypt: Encrypt file with AF-KDF
- decrypt: Decrypt file with AF-KDF
- session: Manage ritual sessions (list, lock, extend)
- profile: View privacy profiles
- recovery: Generate recovery codes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import EchotomeConfig
from .pipeline import run_echotome, encrypt_with_echotome, decrypt_with_echotome
from .privacy_profiles import list_profiles, get_profile, describe_profile
from .sessions import (
    get_session_manager,
    SessionConfig,
)
from .recovery import generate_recovery_codes


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="echotome",
        description="Echotome v3.1 — Ritual Cryptography Engine",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Echotome v3.1.0 (Hardened Edition)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -------------------------------------------------------------------------
    # sigil: Legacy v0.2.0 sigil generation
    # -------------------------------------------------------------------------
    sigil_parser = subparsers.add_parser(
        "sigil",
        help="Generate crypto-sigil from audio (legacy)",
    )
    sigil_parser.add_argument("input_audio", type=str, help="Path to input audio file")
    sigil_parser.add_argument("output_image", type=str, help="Path to output PNG image")
    sigil_parser.add_argument("--key", type=str, required=True, help="Secret passphrase")
    sigil_parser.add_argument("--width", type=int, default=512, help="Image width")
    sigil_parser.add_argument("--height", type=int, default=512, help="Image height")
    sigil_parser.add_argument("--contrast", type=float, default=1.5, help="Contrast boost")
    sigil_parser.add_argument("--json-out", type=str, default="", help="JSON metadata output")

    # -------------------------------------------------------------------------
    # encrypt: Encrypt file with AF-KDF
    # -------------------------------------------------------------------------
    encrypt_parser = subparsers.add_parser(
        "encrypt",
        help="Encrypt a file using Echotome AF-KDF",
    )
    encrypt_parser.add_argument("input_file", type=str, help="File to encrypt")
    encrypt_parser.add_argument("output_file", type=str, help="Encrypted output file")
    encrypt_parser.add_argument("--audio", type=str, required=True, help="Audio file for ritual")
    encrypt_parser.add_argument("--passphrase", type=str, required=True, help="Secret passphrase")
    encrypt_parser.add_argument(
        "--profile",
        type=str,
        default="Ritual Lock",
        choices=["Quick Lock", "Ritual Lock", "Black Vault"],
        help="Privacy profile (default: Ritual Lock)",
    )
    encrypt_parser.add_argument("--sigil", type=str, help="Optional: Save sigil image")

    # -------------------------------------------------------------------------
    # decrypt: Decrypt file with AF-KDF
    # -------------------------------------------------------------------------
    decrypt_parser = subparsers.add_parser(
        "decrypt",
        help="Decrypt a file using Echotome AF-KDF",
    )
    decrypt_parser.add_argument("encrypted_file", type=str, help="Encrypted file to decrypt")
    decrypt_parser.add_argument("output_file", type=str, help="Decrypted output file")
    decrypt_parser.add_argument("--audio", type=str, required=True, help="Audio file for ritual")
    decrypt_parser.add_argument("--passphrase", type=str, required=True, help="Secret passphrase")

    # -------------------------------------------------------------------------
    # session: Session management
    # -------------------------------------------------------------------------
    session_parser = subparsers.add_parser(
        "session",
        help="Manage ritual sessions",
    )
    session_subparsers = session_parser.add_subparsers(dest="session_command")

    # session list
    session_subparsers.add_parser("list", help="List active sessions")

    # session lock <session_id>
    lock_parser = session_subparsers.add_parser("lock", help="Lock (end) a session")
    lock_parser.add_argument("session_id", type=str, help="Session ID to lock")
    lock_parser.add_argument(
        "--no-secure-delete",
        action="store_true",
        help="Skip secure deletion (faster, less secure)",
    )

    # session lock-all
    lock_all_parser = session_subparsers.add_parser("lock-all", help="Lock all sessions (emergency)")
    lock_all_parser.add_argument(
        "--no-secure-delete",
        action="store_true",
        help="Skip secure deletion",
    )

    # session extend <session_id> <seconds>
    extend_parser = session_subparsers.add_parser("extend", help="Extend session TTL")
    extend_parser.add_argument("session_id", type=str, help="Session ID to extend")
    extend_parser.add_argument("seconds", type=int, help="Additional seconds")

    # session cleanup
    session_subparsers.add_parser("cleanup", help="Cleanup expired sessions")

    # -------------------------------------------------------------------------
    # profile: View privacy profiles
    # -------------------------------------------------------------------------
    profile_parser = subparsers.add_parser(
        "profile",
        help="View privacy profile information",
    )
    profile_parser.add_argument(
        "profile_name",
        type=str,
        nargs="?",
        help="Profile name (omit to list all)",
    )

    # -------------------------------------------------------------------------
    # recovery: Generate recovery codes
    # -------------------------------------------------------------------------
    recovery_parser = subparsers.add_parser(
        "recovery",
        help="Generate recovery codes",
    )
    recovery_parser.add_argument("--count", type=int, default=5, help="Number of codes (default: 5)")

    return parser


def cmd_sigil(args: argparse.Namespace) -> int:
    """Generate crypto-sigil (legacy v0.2.0 command)."""
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

    return 0


def cmd_encrypt(args: argparse.Namespace) -> int:
    """Encrypt a file using Echotome AF-KDF."""
    try:
        result = encrypt_with_echotome(
            audio_path=Path(args.audio),
            passphrase=args.passphrase,
            profile_name=args.profile,
            in_file=Path(args.input_file),
            out_file=Path(args.output_file),
            sigil_path=Path(args.sigil) if args.sigil else None,
        )

        print(f"[Echotome] Encrypted: {args.input_file}")
        print(f"[Echotome] Output: {args.output_file}")
        print(f"[Echotome] Profile: {result['profile']}")
        print(f"[Echotome] Rune ID: {result['rune_id']}")

        if args.sigil:
            print(f"[Echotome] Sigil: {args.sigil}")

        return 0

    except Exception as e:
        print(f"[Echotome] Error: {e}", file=sys.stderr)
        return 1


def cmd_decrypt(args: argparse.Namespace) -> int:
    """Decrypt a file using Echotome AF-KDF."""
    try:
        result = decrypt_with_echotome(
            audio_path=Path(args.audio),
            passphrase=args.passphrase,
            blob_file=Path(args.encrypted_file),
            out_file=Path(args.output_file),
        )

        print(f"[Echotome] Decrypted: {args.encrypted_file}")
        print(f"[Echotome] Output: {args.output_file}")
        print(f"[Echotome] Profile: {result['profile']}")
        print(f"[Echotome] Rune ID: {result['rune_id']}")

        return 0

    except ValueError as e:
        print(f"[Echotome] Decryption failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[Echotome] Error: {e}", file=sys.stderr)
        return 1


def cmd_session(args: argparse.Namespace) -> int:
    """Manage ritual sessions."""
    manager = get_session_manager()

    if args.session_command == "list":
        sessions = manager.list_sessions()
        if not sessions:
            print("[Echotome] No active sessions")
            return 0

        print(f"[Echotome] Active sessions: {len(sessions)}")
        print("-" * 60)
        for s in sessions:
            expired = " [EXPIRED]" if s.is_expired() else ""
            print(f"  ID: {s.session_id[:16]}...")
            print(f"  Vault: {s.vault_id}")
            print(f"  Profile: {s.profile}")
            print(f"  Time remaining: {s.format_time_remaining()}{expired}")
            print("-" * 60)
        return 0

    elif args.session_command == "lock":
        session = manager.get_session(args.session_id)
        if not session:
            print(f"[Echotome] Session not found: {args.session_id}", file=sys.stderr)
            return 1

        secure = not args.no_secure_delete
        manager.end_session(args.session_id, secure_delete=secure)
        print(f"[Echotome] Session locked: {args.session_id[:16]}...")
        if secure:
            print("[Echotome] Secure deletion: enabled")
        return 0

    elif args.session_command == "lock-all":
        secure = not args.no_secure_delete
        count = manager.end_all_sessions(secure_delete=secure)
        print(f"[Echotome] Locked {count} session(s)")
        if secure:
            print("[Echotome] Secure deletion: enabled")
        return 0

    elif args.session_command == "extend":
        session = manager.get_session(args.session_id)
        if not session:
            print(f"[Echotome] Session not found: {args.session_id}", file=sys.stderr)
            return 1

        try:
            success = manager.extend_session(args.session_id, args.seconds)
            if success:
                session = manager.get_session(args.session_id)
                print(f"[Echotome] Session extended: {args.session_id[:16]}...")
                print(f"[Echotome] New time remaining: {session.format_time_remaining()}")
                return 0
            else:
                print("[Echotome] Failed to extend session", file=sys.stderr)
                return 1
        except ValueError as e:
            print(f"[Echotome] Error: {e}", file=sys.stderr)
            return 1

    elif args.session_command == "cleanup":
        count = manager.cleanup_expired_sessions()
        print(f"[Echotome] Cleaned up {count} expired session(s)")
        return 0

    else:
        print("[Echotome] Unknown session command. Use: list, lock, lock-all, extend, cleanup")
        return 1


def cmd_profile(args: argparse.Namespace) -> int:
    """View privacy profile information."""
    if args.profile_name:
        try:
            desc = describe_profile(args.profile_name)
            print(f"\n[Echotome] Profile: {desc['name']}")
            print("=" * 50)
            print(f"Threat Model: {desc['threat_model']['id']}")
            print(f"  {desc['threat_model']['description']}")
            print()
            print("Assumptions:")
            print(f"  {desc['threat_model']['assumptions']}")
            print()
            print("Protects Against:")
            print(f"  {desc['threat_model']['protects_against']}")
            print()
            print("Does NOT Protect Against:")
            print(f"  {desc['threat_model']['does_not_protect_against']}")
            print()
            print("KDF Parameters:")
            print(f"  Time: {desc['kdf']['time']} iterations")
            print(f"  Memory: {desc['kdf']['memory']} MB")
            print(f"  Parallelism: {desc['kdf']['parallelism']} threads")
            print()
            print("Session Config:")
            config = SessionConfig.for_profile(args.profile_name)
            print(f"  Default TTL: {config.default_ttl_seconds // 60} minutes")
            print(f"  Max TTL: {config.max_ttl_seconds // 60} minutes")
            print(f"  Auto-lock on background: {config.auto_lock_on_background}")
            print(f"  Secure delete: {config.secure_delete}")
            return 0
        except ValueError as e:
            print(f"[Echotome] Error: {e}", file=sys.stderr)
            return 1
    else:
        profiles = list_profiles()
        print("\n[Echotome] Privacy Profiles")
        print("=" * 50)
        for p in profiles:
            threat_id = getattr(p, "threat_model_id", "unknown")
            print(f"\n{p.name}")
            print(f"  Threat Model: {threat_id}")
            print(f"  Audio Weight: {p.audio_weight * 100:.0f}%")
            print(f"  Deniable: {p.deniable}")
            print(f"  KDF: time={p.kdf_time}, memory={p.kdf_memory}MB")
        print()
        return 0


def cmd_recovery(args: argparse.Namespace) -> int:
    """Generate recovery codes."""
    codes = generate_recovery_codes(count=args.count)

    print("\n[Echotome] Recovery Codes Generated")
    print("=" * 50)
    print("IMPORTANT: Store these codes securely!")
    print("They will NOT be shown again.")
    print()
    for i, code in enumerate(codes, 1):
        print(f"  {i}. {code}")
    print()
    print("=" * 50)
    print(f"Total: {len(codes)} codes")
    return 0


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        # Legacy behavior: if no subcommand but positional args, treat as sigil
        parser.print_help()
        sys.exit(1)

    commands = {
        "sigil": cmd_sigil,
        "encrypt": cmd_encrypt,
        "decrypt": cmd_decrypt,
        "session": cmd_session,
        "profile": cmd_profile,
        "recovery": cmd_recovery,
    }

    if args.command in commands:
        exit_code = commands[args.command](args)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


# Legacy entry point for backward compatibility
def parse_args() -> argparse.Namespace:
    """Legacy argument parser (v0.2.0 compatibility)."""
    parser = argparse.ArgumentParser(
        description="Echotome — audio → crypto-sigil engine",
    )
    parser.add_argument("input_audio", type=str, help="Path to input audio file")
    parser.add_argument("output_image", type=str, help="Path to output PNG image")
    parser.add_argument("--key", type=str, required=True, help="Secret passphrase")
    parser.add_argument("--width", type=int, default=512, help="Image width")
    parser.add_argument("--height", type=int, default=512, help="Image height")
    parser.add_argument("--contrast", type=float, default=1.5, help="Contrast boost")
    parser.add_argument("--json-out", type=str, default="", help="JSON metadata output")
    return parser.parse_args()


if __name__ == "__main__":
    main()
