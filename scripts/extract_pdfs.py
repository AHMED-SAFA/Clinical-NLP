import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimscribe.config import PROTOCOLS
from aimscribe.extract import extract_protocol

for k in PROTOCOLS:
    out = extract_protocol(k)
    flag = [p for p, v in out["pages"].items() if v["inspect_png"]]
    print(f"{k}: {len(out['pages'])} pages | low-text pages (read the PNG): {flag}")
