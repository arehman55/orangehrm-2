"""Retry-aware Robot Framework runner used locally and in CI."""

from __future__ import annotations

import os
from pathlib import Path
from robot import rebot, run


def run_robot_suite(
    robot_file: Path,
    output_dir: Path,
    browser: str,
    headless: bool,
    retries: int = 1,
) -> int:
    """Run the RPA suite and rerun failed tasks up to ``retries`` times."""
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(
        "ALLURE_RESULTS_DIRECTORY", str(output_dir / "allure-results")
    )
    output_file = output_dir / "output.xml"
    listener = "src.reporting.AllureFailureListener"
    common_options: list[str] = [
        str(robot_file),
        "--outputdir",
        str(output_dir),
        "--listener",
        "allure_robotframework",
        "--listener",
        listener,
        "--variable",
        f"BROWSER:{browser}",
        "--variable",
        f"HEADLESS:{str(headless).lower()}",
    ]

    exit_code = int(run(*common_options, output=str(output_file)))
    for attempt in range(1, retries + 1):
        if exit_code == 0:
            break
        retry_output = output_dir / f"retry-{attempt}.xml"
        exit_code = int(
            run(
                str(robot_file),
                "--rerunfailed",
                str(output_file),
                "--outputdir",
                str(output_dir),
                "--output",
                str(retry_output),
                "--listener",
                "allure_robotframework",
                "--listener",
                listener,
                "--variable",
                f"BROWSER:{browser}",
                "--variable",
                f"HEADLESS:{str(headless).lower()}",
            )
        )
        rebot(
            str(output_file),
            str(retry_output),
            merge=True,
            outputdir=str(output_dir),
            output=str(output_file),
        )

    return exit_code
