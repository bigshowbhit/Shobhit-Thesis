import hashlib, os
from pathlib import Path
import shutil

def atomic_symlink_update(target_path: Path, link_path: Path):
    # Ensure target exists
    if not target_path.exists():
        raise FileNotFoundError(f"Target for symlink does not exist: {target_path}")

    # Ensure link parent exists
    link_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a temp path alongside the link (safer than with_suffix)
    tmp = link_path.with_name(link_path.name + ".tmp")

    # Clean any stale temp (file, symlink, or dir)
    if os.path.lexists(tmp):
        if os.path.islink(tmp) or os.path.isfile(tmp):
            os.unlink(tmp)
        elif os.path.isdir(tmp):
            shutil.rmtree(tmp)

    # If the final path is a real directory, remove it (or raise)
    if os.path.isdir(link_path) and not os.path.islink(link_path):
        # choose your policy: raise or remove; removing is convenient:
        shutil.rmtree(link_path)

    # Create temp symlink and atomically swap
    os.symlink(target_path, tmp)
    os.replace(tmp, link_path)  # overwrites file/symlink atomically

def ensure_dirs(*dirs: Path):

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()