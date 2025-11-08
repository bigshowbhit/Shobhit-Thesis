from pathlib import Path
import hashlib, os, shutil, time

def atomic_symlink_update(target_path: Path, current_ver: Path):

    temp = current_ver.with_suffix(".tmp")
    if temp.exists() or temp.is_symlink():
        temp.unlink()
    
    os.symlink(target_path, temp)
    os.replace(temp, current_ver)

