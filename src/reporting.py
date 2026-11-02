"""Robot Framework reporting hooks and failure evidence."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import allure
from robot.api import logger as robot_logger

logger = logging.getLogger(__name__)
_current_driver: Any | None = None


def register_driver(driver: Any) -> None:
    """Register the active Selenium driver for the suite listener."""
    global _current_driver
    _current_driver = driver


def unregister_driver() -> None:
    """Release the active Selenium driver after suite teardown."""
    global _current_driver
    _current_driver = None


class AllureFailureListener:
    """Attach a Selenium screenshot to Allure whenever a task fails."""

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self) -> None:
        self.output_dir = Path(os.getenv("ROBOT_OUTPUT_DIR", "output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def end_test(self, data: Any, result: Any) -> None:
        if result.status != "FAIL" or _current_driver is None:
            return

        filename = f"failure-{self._safe_name(result.name)}.png"
        screenshot_path = self.output_dir / filename
        try:
            if _current_driver.save_screenshot(str(screenshot_path)):
                allure.attach.file(
                    str(screenshot_path),
                    name=f"{result.name} screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
                robot_logger.info(
                    f"Attached failure screenshot to Allure: {screenshot_path}",
                    also_console=False,
                )
        except Exception as exc:  # reporting must never mask the test failure
            logger.warning("Could not attach failure screenshot: %s", exc)

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(character if character.isalnum() else "_" for character in name)
