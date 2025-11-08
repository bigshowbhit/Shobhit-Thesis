from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config.yaml"
PUBK = ROOT / "public.pem"
STAGING = ROOT / "staging"  # (Temp) )Directory where new firmware versions are downloaded & verified
STATE = ROOT / "state"  # Directory where the real version is stored
CURRENT = ROOT / "current"  # A symlink to the current firmware version