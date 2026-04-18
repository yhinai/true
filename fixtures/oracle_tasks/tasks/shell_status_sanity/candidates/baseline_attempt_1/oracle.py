from pathlib import Path
import sys

content = Path("status.txt").read_text(encoding="utf-8").strip()
sys.exit(0 if content == "OK" else 1)
