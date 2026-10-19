import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aimscribe.indexer import build_index

print(f"Indexed {build_index()} cards")
