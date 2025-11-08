import yaml
from .paths import CFG

def load_config():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)