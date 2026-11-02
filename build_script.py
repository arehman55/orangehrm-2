"""Build a wheel from a clean local build and distribution directory."""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Remove previous artifacts and build a fresh wheel.

    Example:
        >>> main()
    """
    for directory_name in ("build", "dist"):
        directory = PROJECT_ROOT / directory_name
        if directory.exists():
            shutil.rmtree(directory)

    subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
