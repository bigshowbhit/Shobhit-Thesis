import json, shutil, sys, time
from pathlib import Path
from .paths import ROOT, STAGING, STATE, CURRENT
from .config import load_config
from .http_util import get_json, download
from .crypto import load_public_key, verify_metadata_signature
from .util import ensure_dirs, sha256_file, atomic_symlink_update

class Updater:

    def __init__(self):
        self.config = load_config()
        self.server = self.config["server_url"].rstrip("/")
        self.device_id = self.config.get("device_id", "dev-001")
        self.VERIFY = (ROOT / self.config.get("tls_ca_cert")).as_posix() if self.config.get("tls_ca_cert") else True

    def get_current_version(self) -> str | None:
        current_file = Path('/app/client/current_base/current.txt')
        if current_file.exists():
            try:
                version = current_file.read_text(encoding='utf-8').strip()
                if version and self.is_installed(version):
                    return version
            except Exception:
                pass
        return None
    
    def is_installed(self, version: str) -> bool:
        d = STATE / version
        return d.is_dir() and (d / "firmware.bin").exists() and (d / "sha256.txt").exists()

    def set_version(self, version: str):

        target_path = STATE / version
        if target_path.exists():
            current_file = Path('/app/client/current_base/current.txt')
            current_file.write_text(version + '\n', encoding='utf-8')
            #atomic_symlink_update(target_path, CURRENT)
        else:
            raise RuntimeError(f"Version {version} does not exist in state directory.")

    def run(self):
        # Main update logic 
        ensure_dirs(STAGING, STATE)
        #get teh current version
        current_version = self.get_current_version() or self.config.get("current_version") or "none"

        if current_version not in (None, "none") and not self.is_installed(current_version):
            print(f"[warn] local payload for {current_version} missing; treating as none")
            current_version = "none"
            
            # Optional: if CURRENT is dangling, remove it so we can recreate it later
            if CURRENT.is_symlink():
                try:
                    CURRENT.resolve(strict=True)
                except FileNotFoundError:
                    CURRENT.unlink()

        print(f"Current version: {current_version}")
        # if CURRENT.exists():
        #     print(f"[debug] CURRENT exists, is_symlink={CURRENT.is_symlink()}")
        # if CURRENT.is_symlink():
        #     print(f"[debug] CURRENT -> {CURRENT.resolve()}")

        # Check if the current version is up to date

        try:
            info = get_json(f"{self.server}/check",
                            params={"current": current_version, "deviceId": self.device_id}, verify=self.VERIFY)

        except Exception as e:
            print(f"[check] failed: {e}")
            sys.exit(1)

        target = info.get("target") or info.get("latest") or info.get("version")
        if target == current_version:
            print(f"[check] up-to-date (current={current_version})")
            return
        # then the update is available & follow the steps to download & install it
        print(f"[check] update available: {current_version} -> {target}")

        # 1 - Get the metadata
        try:
            md = get_json(f"{self.server}/versions/{target}/metadata", verify=self.VERIFY)
        except Exception as e:
            print(f"[metadata] fetch failed: {e}")
            sys.exit(1)

        # 2 - Verifyt he metadata.json signature by the public key and extract the expected sha256
        try:
            pub = load_public_key()
            verify_metadata_signature(md, pub)
        except Exception as e:
            print(f"[metadata] signature INVALID: {e}")
            sys.exit(1)
        print("[metadata] signature valid")
        sha_expected = md.get("sha256")
        if not sha_expected:
            print("[metadata] missing sha256")
            sys.exit(1)

        # 3 - Download to STAGING directory
        fw_url = f"{self.server}/versions/{target}/download"
        staging_bin = STAGING / f"firmware-{target}.bin"
        try:
            download(fw_url, staging_bin, verify=self.VERIFY)
        except Exception as e:
            print(f"[download] failed: {e}")
            sys.exit(1)

        # 4 - Verify sha256
        sha_actual = sha256_file(staging_bin)
        if sha_actual.lower() != sha_expected.lower():
            print(f"[verify] SHA mismatch: expected {sha_expected}, got {sha_actual}")
            staging_bin.unlink(missing_ok=True)
            sys.exit(1)
        print("[verify] file hash OK")

        # 5- Move to STATE directory
        final_path = STATE / target                       
        final_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging_bin), str(final_path / "firmware.txt"))
        (final_path / "sha256.txt").write_text(sha_actual + "\n", encoding="utf-8")
        (final_path / "installed_at").write_text(time.strftime("%Y-%m-%dT%H:%M:%S%z") + "\n", encoding="utf-8")
        (final_path / "metadata.json").write_text(json.dumps(md, indent=2), encoding="utf-8")

        # 6 - Atomic update of the symlink & Activate the new version
        self.set_version(target)
        print(f"[install] activated {target}")
        self.config.pop("current_version", None) 
