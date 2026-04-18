from pathlib import Path
import sys

content = Path("answer.txt").read_text(encoding="utf-8").strip()
sys.exit(0 if content == "SQUARE=144" else 1)
