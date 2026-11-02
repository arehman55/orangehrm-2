"""Unit tests for page locators, base waits, and the wheel build script."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from openpyxl import Workbook
from selenium.common.exceptions import TimeoutException, WebDriverException

import build_script
from src import config
from src.base_page import BasePage
from src.pages.locators import MyInfoLocators
from src.pages.my_info_page import MyInfoPage
from src.services.thunderbird_mailer import ThunderbirdMailer


class MyInfoPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = MyInfoPage.__new__(MyInfoPage)
        self.page.click_element = Mock()
        self.page.wait_for_loaders = Mock()

    def test_open_sub_tab_uses_external_locator(self) -> None:
        self.page.open_sub_tab("Personal Details")

        self.page.click_element.assert_called_once_with(
            MyInfoLocators.tab_link("Personal Details")
        )
        self.page.wait_for_loaders.assert_called_once_with()

    def test_xpath_literal_supports_apostrophes(self) -> None:
        locator = MyInfoLocators.tab_link("Driver's License")

        self.assertEqual(locator[0], "xpath")
        self.assertIn("concat(", locator[1])
        self.assertIn("Driver", locator[1])
        self.assertIn("License", locator[1])

    def test_scrape_generic_section_table_returns_rows(self) -> None:
        cells = [
            SimpleNamespace(text=""),
            SimpleNamespace(text="Acme"),
            SimpleNamespace(text="Engineer"),
        ]
        row = Mock()
        row.find_elements.return_value = cells
        self.page.driver = Mock()
        self.page.driver.find_elements.return_value = [row]

        result = self.page._scrape_generic_section_table(
            "Work Experience", ["Company", "Job Title"]
        )

        self.assertEqual(result, [{"Company": "Acme", "Job Title": "Engineer"}])
        self.page.driver.find_elements.assert_called_once_with(
            *MyInfoLocators.generic_section_rows("Work Experience")
        )
        row.find_elements.assert_called_once_with(*MyInfoLocators.ATTACHMENT_CELL)


class BasePageTests(unittest.TestCase):
    def test_loader_wait_uses_only_configured_explicit_wait(self) -> None:
        page = BasePage.__new__(BasePage)
        page.wait = Mock()
        page.wait_for_loaders()

        self.assertEqual(page.wait.until.call_count, 2)

    def test_capture_attachment_returns_no_attachment_after_timeout(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.wait_for_loaders = Mock()

        with patch("src.mixins.attachment_mixin.WebDriverWait") as wait_class:
            wait_class.return_value.until.side_effect = TimeoutException()
            with self.assertLogs(
                "src.mixins.attachment_mixin", level="WARNING"
            ) as logs:
                result = page.capture_attachment_metadata_from_current_section("Job")

        self.assertEqual(result["Download_Status"], "No Attachment Found")
        self.assertTrue(
            all(
                value == "N/A"
                for value in result.values()
                if value != result["Download_Status"]
            )
        )
        self.assertIn("timed out", logs.output[0])

    def test_capture_attachment_logs_webdriver_failure(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.wait_for_loaders = Mock()

        with patch("src.mixins.attachment_mixin.WebDriverWait") as wait_class:
            wait_class.return_value.until.side_effect = WebDriverException(
                "driver offline"
            )
            with self.assertLogs("src.mixins.attachment_mixin", level="ERROR") as logs:
                result = page.capture_attachment_metadata_from_current_section("Job")

        self.assertEqual(result["Download_Status"], "No Attachment Found")
        self.assertIn("driver offline", logs.output[0])


class BuildScriptTests(unittest.TestCase):
    def test_main_cleans_artifacts_and_builds_wheel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "build").mkdir()
            (project_root / "dist").mkdir()

            with (
                patch.object(build_script, "PROJECT_ROOT", project_root),
                patch.object(build_script.shutil, "rmtree") as rmtree,
                patch.object(build_script.subprocess, "run") as run,
            ):
                build_script.main()

        self.assertEqual(
            rmtree.call_args_list,
            [
                unittest.mock.call(project_root / "build"),
                unittest.mock.call(project_root / "dist"),
            ],
        )
        run.assert_called_once_with(
            [sys.executable, "-m", "build", "--wheel"],
            cwd=project_root,
            check=True,
        )


class ThunderbirdMailerTests(unittest.TestCase):
    def test_details_attachment_uses_absolute_filesystem_path(self) -> None:
        config.validate_environment()
        mailer = ThunderbirdMailer.__new__(ThunderbirdMailer)
        mailer._build_details_reply_html = Mock(return_value="<p>Details</p>")
        mailer._compose_and_dispatch = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            details_path = Path(temp_dir) / "Details.xlsx"
            workbook = Workbook()
            workbook.active.append(["Section", "Status"])
            workbook.save(details_path)

            mailer.send_reply_with_details_excel(details_path)

        compose_arg = mailer._compose_and_dispatch.call_args.args[0]

        secured_excel_path = details_path.with_name("Details_protected.xlsx")

        # Verify that the Thunderbird command contains the absolute path to the encrypted workbook
        self.assertIn(
            f"attachment='{os.path.abspath(secured_excel_path)}'", compose_arg
        )

        # Ensure that no raw 'file://' protocols are passed to the compose argument
        self.assertNotIn("file://", compose_arg)

    def test_compose_removes_conda_library_variables(self) -> None:
        mailer = ThunderbirdMailer.__new__(ThunderbirdMailer)
        mailer.tb_exe = "thunderbird"
        mailer.timeout = 20
        mailer.desktop = Mock()
        window_backend = MagicMock()
        window_backend.__enter__.return_value = window_backend
        window_backend.find_window.return_value = Mock()
        window_backend.is_active.return_value = True
        window_backend.is_open.return_value = False

        with (
            patch.dict(
                os.environ,
                {
                    "LD_LIBRARY_PATH": "/conda/lib",
                    "LD_PRELOAD": "/conda/lib/libc.so.6",
                    "PYTHONPATH": "/conda/python",
                    "PYTHONHOME": "/conda",
                    "GIO_MODULE_DIR": "/home/user/snap/code/gio-modules",
                    "GTK_PATH": "/snap/code/usr/lib/gtk-3.0",
                },
                clear=False,
            ),
            patch("src.services.thunderbird_mailer.subprocess.Popen") as popen,
            patch.object(
                ThunderbirdMailer, "_open_window_backend", return_value=window_backend
            ),
            patch("src.services.thunderbird_mailer.COMPOSE_SETTLE_SECONDS", 0),
            patch("src.services.thunderbird_mailer.FOCUS_RETRY_SECONDS", 0),
        ):
            # Configure mock Popen process to safely handle standard library calls
            mock_process = popen.return_value
            mock_process.communicate.return_value = (b"", b"")
            mock_process.__enter__.return_value = mock_process

            mailer._compose_and_dispatch("to='test@example.com'")

        child_environment = popen.call_args.kwargs["env"]
        self.assertNotIn("LD_LIBRARY_PATH", child_environment)
        self.assertNotIn("LD_PRELOAD", child_environment)
        self.assertNotIn("PYTHONPATH", child_environment)
        self.assertNotIn("PYTHONHOME", child_environment)
        self.assertNotIn("GIO_MODULE_DIR", child_environment)
        self.assertNotIn("GTK_PATH", child_environment)
        window_backend.find_window.assert_called_once_with("Write:")
        window_backend.activate.assert_called_once_with(
            window_backend.find_window.return_value
        )
        mailer.desktop.press_keys.assert_called_once_with("ctrl", "enter")
        popen.assert_called_once_with(
            ["thunderbird", "-compose", "to='test@example.com'"],
            env=child_environment,
        )


if __name__ == "__main__":
    unittest.main()
