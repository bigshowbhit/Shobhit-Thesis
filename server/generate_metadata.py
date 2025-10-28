#!/usr/bin/env python3
import argparse, base64, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

HERE = Path(__file__).resolve().parent
KEYS_DIR = HERE.parent / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private.pem"

def sha256_file(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_private_key():
    """Load RSA private key from PEM file."""
    pem = PRIVATE_KEY_PATH.read_bytes()
    return serialization.load_pem_private_key(pem, password=None)

def sign_bytes(priv, data: bytes) -> str:
    """Sign data with RSA-PSS and return base64 signature."""
    sig = priv.sign(
        data,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("ascii")

def canonical_json(obj) -> bytes:
    """Return canonical JSON for signing (sorted keys, no spaces)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def main():
    p = argparse.ArgumentParser(description="Generate signed metadata.json for a version (auto-create if missing).")
    p.add_argument("version", help="Version folder name (e.g., v1, v2)")
    p.add_argument("--file", default="firmware.txt", help="Firmware file name in the version dir")
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting existing metadata.json")
    args = p.parse_args()

    vdir = HERE / args.version
    fw = vdir / args.file
    meta_path = vdir / "metadata.json"

    # Create version directory if missing
    if not vdir.exists():
        vdir.mkdir(parents=True)
        print(f"[INFO] Created version directory: {vdir}")

    # Create dummy firmware.txt if missing
    if not fw.exists():
        fw.write_text(f"This is {args.version} firmware content", encoding="utf-8")
        print(f"[INFO] Created dummy firmware file: {fw}")

    # Prevent accidental overwrite
    if meta_path.exists() and not args.overwrite:
        raise SystemExit(f"[!] {meta_path} exists. Use --overwrite to replace.")

    # 1️⃣ Compute SHA-256 hash
    digest = sha256_file(fw)

    # 2️⃣ Build unsigned metadata
    metadata_unsigned = {
        "version": args.version,
        "file": args.file,
        "sha256": digest,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # 3️⃣ Sign metadata
    priv = load_private_key()
    signature_b64 = sign_bytes(priv, canonical_json(metadata_unsigned))

    # 4️⃣ Write final signed metadata.json
    metadata = dict(metadata_unsigned)
    metadata["signature"] = signature_b64
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"[OK] metadata.json created and signed at {meta_path}")
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()