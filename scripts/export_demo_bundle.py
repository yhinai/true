from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


if __name__ == "__main__":
    main()
