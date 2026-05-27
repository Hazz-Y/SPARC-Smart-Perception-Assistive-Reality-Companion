from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any, Dict

# Per-user config file under ~/.config/sparc/config.json
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "sparc"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: Dict[str, Any] = {
    "audio": {
        "preferred_mic_name": "",   # substring match (e.g., "bluez_input")
        "preferred_mic_index": None # exact SR index
    },
    "display": {
        "rotation": 0,              # 0, 90, 180, 270
        "scan_dir": "auto",         # "auto" | "normal" | "reverse"
        "offset_x": 0,
        "offset_y": 0,
        "line_height_large": 18,
        "line_height_med": 14,
        "use_border": True
    }
}

def load_config() -> Dict[str, Any]:
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # merge with defaults (shallow)
            cfg = DEFAULTS.copy()
            for k,v in (data or {}).items():
                if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                    tmp = cfg[k].copy()
                    tmp.update(v)
                    cfg[k] = tmp
                else:
                    cfg[k] = v
            return cfg
    except Exception:
        pass
    return DEFAULTS.copy()

def save_config(cfg: Dict[str, Any]) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
    except Exception:
        pass

