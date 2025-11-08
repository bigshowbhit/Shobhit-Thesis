import json, shutil, sys, time
from .config import load_config
from pathlib import Path 
from .paths import STAGING, STATE, CURRENT
from .util import atomic_symlink_update


class Updater:

    def __init__(self):

        self.configFile = load_config()
        self.server = self.configFile["server_url"].rstrip("/")
        self.device_id = self.configFile.get("device_id", "dev-001")

    def get_current_version(self) -> str | None:

        if CURRENT.is_symlink():

            try:
                current_version = CURRENT.resolve()
                if current_version.parent == STATE: # Ensure it points to STATE directory as the state directory contains the run-time or current firmware versions
                    return current_version.name
            except FileNotFoundError:
                pass
        return None

    def set_version(self, version: str):

        target_path = STATE / version
        if target_path.exists():
            atomic_symlink_update(target_path, CURRENT)
        else:
            raise RuntimeError(f"Version {version} does not exist in state directory.")

    def run(self):
        # Main update logic 

        pass
        



