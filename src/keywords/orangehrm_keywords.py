"""
Robot Framework Keyword Library bridging tasks.robot with the modular Page Object Model.
Manages browser initialization, custom exceptions, screenshots on failure, and safe teardown.
Exports strictly 2 Excel workbooks:
1. OrangeHRM_Data.xlsx (Timesheets)
2. Details.xlsx (10 My Info Worksheets, each with its own Attachments section & PDF hyperlinks)
"""

from __future__ import annotations

import logging
import platform

from robot.api.deco import keyword, library
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from src.config import (
    BASE_URL,
    MY_INFO_SECTIONS,
    MY_INFO_SECTIONS_DATA,
    OUTPUT_DIR,
    PASSWORD,
    BROWSER,
    HEADLESS,
    SAMPLE_ATTACHMENT_PATH,
    TIMESHEET_DATA,
    USERNAME,
    WAIT_TIMEOUT,
    format_my_info_section_label,
)
from src.decorators import requires_driver
from src.excel_manager import ExcelManager
from src.exceptions import (
    AuthenticationError,
    EmailAutomationError,
    MyInfoAutomationError,
    TimesheetAutomationError,
)
from src.pages.login_page import LoginPage
from src.pages.my_info_page import MyInfoPage
from src.pages.time_page import TimePage
from src.reporting import register_driver, unregister_driver
from src.services.thunderbird_mailer import ThunderbirdMailer

logger = logging.getLogger(__name__)


@library(scope="GLOBAL", auto_keywords=False)
class OrangeHRMKeywords:
    """Enterprise Keyword Library for OrangeHRM End-to-End RPA."""

    def __init__(self) -> None:
        """Initialize the keyword library without opening a browser.

        Args:
            None.

        Returns:
            None.

        Example:
            keywords = OrangeHRMKeywords()
        """
        self.driver: webdriver.Chrome | None = None

    @keyword("Initialize Browser Session")
    def initialize_browser_session(self, headless: bool = HEADLESS, browser: str = BROWSER) -> None:
        """Start a configured Selenium Chrome WebDriver session.

        Args:
            headless (bool): Whether to run Chrome without a visible window.

        Returns:
            None.

        Example:
            keywords.initialize_browser_session(headless=True)
        """
        browser = browser.lower()
        if browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("-headless")
            self.driver = webdriver.Firefox(options=options)
        elif browser == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            if platform.system() == "Linux":
                options.add_argument("--ozone-platform=x11")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            self.driver = webdriver.Chrome(options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        register_driver(self.driver)
        logger.info("%s WebDriver session initialized successfully.", browser)

    @keyword("Execute Phase 1 Authentication")
    @requires_driver
    def execute_phase_1_authentication(self) -> None:
        try:
            login_page = LoginPage(self.driver, timeout=WAIT_TIMEOUT)
            login_page.login(BASE_URL, USERNAME, PASSWORD)
        except AuthenticationError:
            self._capture_failure_state("phase1_auth_failure")
            raise
        except (OSError, RuntimeError, ValueError, WebDriverException) as exc:
            self._capture_failure_state("phase1_auth_failure")
            raise AuthenticationError(f"Phase 1 Authentication failed: {exc}") from exc

    @keyword("Execute Phase 2 Time Module Automation And Scraping")
    @requires_driver
    def execute_phase_2_time_module(self) -> None:
        """
        Execute timesheet automation and export the resulting workbook.

        Args:
            None.

        Returns:
            None.

        Example:
            keywords.execute_phase_2_time_module()
        """
        try:
            time_page = TimePage(self.driver, timeout=WAIT_TIMEOUT)
            time_page.navigate_to_my_timesheets()
            time_page.enter_and_save_timesheet(TIMESHEET_DATA)
            scraped_timesheet = time_page.scrape_saved_timesheet()

            timesheet_excel_path = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
            if timesheet_excel_path.exists():
                timesheet_excel_path.unlink()

            # Workbook 1: OrangeHRM_Data.xlsx (Strictly Timesheet Data)
            ExcelManager.save_to_sheet(
                file_path=timesheet_excel_path,
                sheet_name="Timesheet_Data",
                data=scraped_timesheet,
            )
        except TimesheetAutomationError:
            self._capture_failure_state("phase2_time_failure")
            raise
        except (OSError, RuntimeError, ValueError, WebDriverException) as exc:
            self._capture_failure_state("phase2_time_failure")
            raise TimesheetAutomationError(
                f"Phase 2 Time Module failed: {exc}"
            ) from exc

    @keyword("Execute Phase 3 My Info Automation And Scraping")
    @requires_driver
    def execute_phase_3_my_info_module(self) -> None:
        """
        Execute My Info automation and export the details workbook.

        Args:
            None.

        Returns:
            None.

        Example:
            keywords.execute_phase_3_my_info_module()
        """
        try:
            my_info_page = MyInfoPage(self.driver, timeout=WAIT_TIMEOUT)
            sections_map, attachments_by_section = (
                my_info_page.process_all_ten_sections(
                    sections_data=MY_INFO_SECTIONS_DATA,
                    attachment_file=SAMPLE_ATTACHMENT_PATH,
                )
            )

            details_excel_path = OUTPUT_DIR / "Details.xlsx"
            if details_excel_path.exists():
                details_excel_path.unlink()

            # Remove legacy Attachments.xlsx if it exists from previous runs so only 2 Excel files remain
            legacy_attachments_path = OUTPUT_DIR / "Attachments.xlsx"
            if legacy_attachments_path.exists():
                legacy_attachments_path.unlink()

            section_to_attachment_key = {
                section_name: format_my_info_section_label(section_name, position)
                for position, section_name in enumerate(MY_INFO_SECTIONS, start=1)
            }

            # Workbook 2: Details.xlsx (10 Worksheets, each with Section Data + Attachments + Hyperlink)
            for sheet_name, section_rows in sections_map.items():
                att_key = section_to_attachment_key.get(sheet_name, "")
                att_rows = attachments_by_section.get(att_key, [])

                ExcelManager.save_section_with_attachments(
                    file_path=details_excel_path,
                    sheet_name=sheet_name,
                    section_data=section_rows,
                    attachments_data=att_rows,
                    pdf_path=SAMPLE_ATTACHMENT_PATH,
                )

        except MyInfoAutomationError:
            self._capture_failure_state("phase3_my_info_failure")
            raise
        except (OSError, RuntimeError, ValueError, WebDriverException) as exc:
            self._capture_failure_state("phase3_my_info_failure")
            raise MyInfoAutomationError(
                f"Phase 3 My Info Module failed: {exc}"
            ) from exc

    @keyword("Execute Phase 4 Email Reporting Via Thunderbird")
    def execute_phase_4_email_reporting(self) -> None:
        """
        Send the timesheet report and details reply through Thunderbird.

        Args:
            None.

        Returns:
            None.

        Example:
            keywords.execute_phase_4_email_reporting()
        """
        try:
            mailer = ThunderbirdMailer()
            timesheet_excel = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
            details_excel = OUTPUT_DIR / "Details.xlsx"

            mailer.send_timesheet_html_email(timesheet_excel)
            mailer.send_reply_with_details_excel(details_excel)
        except EmailAutomationError:
            raise
        except (OSError, RuntimeError, ValueError) as exc:
            raise EmailAutomationError(
                f"Phase 4 Thunderbird Email Reporting failed: {exc}"
            ) from exc

    @keyword("Close Browser Safely")
    def close_browser_safely(self) -> None:
        """Close the WebDriver session during suite teardown.

        Args:
            None.

        Returns:
            None.

        Example:
            keywords.close_browser_safely()
        """
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed cleanly.")
            except WebDriverException as exc:
                logger.warning("Error while closing WebDriver: %s", exc)
            finally:
                self.driver = None
                unregister_driver()

    def _capture_failure_state(self, prefix: str) -> None:
        """Save a diagnostic screenshot after a workflow failure.

        Args:
            prefix (str): Prefix for the screenshot filename.

        Returns:
            None.

        Example:
            keywords._capture_failure_state("phase1_failure")
        """
        if self.driver:
            screenshot_path = OUTPUT_DIR / f"{prefix}.png"
            try:
                self.driver.save_screenshot(str(screenshot_path))
                logger.error("Saved diagnostic screenshot to %s", screenshot_path)
            except WebDriverException as exc:
                logger.warning(
                    "Could not save diagnostic screenshot to %s: %s",
                    screenshot_path,
                    exc,
                )
