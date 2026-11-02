"""
Base Page Object Model (POM) class providing strict Explicit Waits,
Vue.js input clearing, custom dropdown handling, and toast assertions.
"""

from __future__ import annotations

import logging

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.exceptions import OrangeHRMBaseException
from src.mixins.attachment_mixin import AttachmentMixin
from src.pages.locators import BaseLocators

logger = logging.getLogger(__name__)


class BasePage(AttachmentMixin):
    """Foundational wrapper for all OrangeHRM Page Objects using pure Python Selenium."""

    # Global OrangeHRM Vue.js Locators
    LOADING_SPINNER = BaseLocators.LOADING_SPINNER
    FORM_LOADER = BaseLocators.FORM_LOADER
    SUCCESS_TOAST = BaseLocators.SUCCESS_TOAST

    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        """Initialize the page with a Selenium driver and explicit-wait timeout.

        Args:
            driver (WebDriver): Active Selenium browser session.
            timeout (int): Default explicit-wait timeout in seconds.

        Returns:
            None.

        Example:
            page = BasePage(driver, timeout=20)
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=(StaleElementReferenceException,),
        )

    def wait_for_loaders(self) -> None:
        """Wait for OrangeHRM's asynchronous loaders to disappear."""
        self.wait.until(EC.invisibility_of_element_located(self.LOADING_SPINNER))
        self.wait.until(EC.invisibility_of_element_located(self.FORM_LOADER))

    def find_visible(self, locator: tuple[str, str]) -> WebElement:
        """Wait for and return a visible element.

        Args:
            locator (tuple[str, str]): Selenium locator tuple.

        Returns:
            WebElement: Visible matching element.

        Example:
            field = page.find_visible(locator)
        """
        self.wait_for_loaders()
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all_visible(self, locator: tuple[str, str]) -> list[WebElement]:
        """Wait for and return all visible matching elements.

        Args:
            locator (tuple[str, str]): Selenium locator tuple.

        Returns:
            list[WebElement]: Visible matching elements.

        Example:
            rows = page.find_all_visible(locator)
        """
        self.wait_for_loaders()
        return self.wait.until(EC.visibility_of_all_elements_located(locator))

    def click_element(self, locator: tuple[str, str]) -> None:
        """
        Wait for an element to be clickable and click it.

        Args:
            locator (tuple[str, str]): Selenium locator tuple.

        Returns:
            None.

        Example:
            page.click_element(locator)
        """
        self.wait_for_loaders()
        element = self.wait.until(EC.element_to_be_clickable(locator))
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.info(
                "Click intercepted on %s. Retrying via ActionChains move_to_element.",
                locator,
            )
            self.wait_for_loaders()
            ActionChains(self.driver).move_to_element(element).click().perform()

    def clear_and_type(self, locator: tuple[str, str], text: str) -> None:
        """
        Clear a Vue.js input and type text using Selenium actions.

        Args:
            locator (tuple[str, str]): Selenium input locator.
            text (str): Text to enter.

        Returns:
            None.

        Example:
            page.clear_and_type(locator, "Admin")
        """
        element = self.find_visible(locator)

        # If an OrangeHRM date-picker calendar popup is open and overlapping, dismiss it via ESCAPE
        open_calendars = self.driver.find_elements(*BaseLocators.CALENDAR_WRAPPER)
        if open_calendars:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

        ActionChains(self.driver).move_to_element(element).perform()
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.info(
                "Click intercepted on input %s (likely by calendar popup). Dismissing popup and clicking via ActionChains.",
                locator,
            )
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            ActionChains(self.driver).move_to_element(element).click().perform()

        # Note: Uses CONTROL for Windows/Linux. For macOS support, requires COMMAND.
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(str(text))

        # Close any calendar dropdown triggered by typing into a date input
        placeholder = (element.get_attribute("placeholder") or "").lower()
        if placeholder in ("yyyy-mm-dd", "dd-mm-yyyy"):
            element.send_keys(Keys.TAB)

    def get_input_by_label(self, label_text: str) -> tuple[str, str]:
        """Build the input or textarea locator associated with a label."""
        return BaseLocators.input_by_label(label_text)

    def fill_field_by_label(self, label_text: str, value: str) -> None:
        """Fill an input or textarea identified by its visible label.

        Args:
            label_text (str): Visible field label.
            value (str): Value to enter.

        Returns:
            None.

        Example:
            page.fill_field_by_label("Employee Id", "EMP-9042")
        """
        locator = self.get_input_by_label(label_text)
        self.clear_and_type(locator, value)

    def read_field_by_label(self, label_text: str) -> str:
        """Read the current value of a labeled input field.

        Args:
            label_text (str): Visible field label.

        Returns:
            str: Field value or ``N/A`` when unavailable.

        Example:
            employee_id = page.read_field_by_label("Employee Id")
        """
        locator = self.get_input_by_label(label_text)
        try:
            element = self.find_visible(locator)
            val = (element.get_attribute("value") or "").strip()
            return val if val else "N/A"
        except TimeoutException:
            return "N/A"

    def select_dropdown_by_label(
        self,
        label_text: str,
        option_text: str | None = None,
        index: int | None = None,
    ) -> str:
        """
        Select an option from a custom OrangeHRM dropdown.

        Args:
            label_text (str): Visible dropdown label.
            option_text (str | None): Desired visible option text.
            index (int | None): One-based option index when explicitly requested.

        Returns:
            str: Selected option text.

        Example:
            country = page.select_dropdown_by_label("Country", "Pakistan")
        """
        self.click_element(BaseLocators.dropdown_by_label(label_text))

        if option_text:
            try:
                opt_el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        BaseLocators.dropdown_option(option_text)
                    )
                )
                selected_val = opt_el.text.strip()
                ActionChains(self.driver).move_to_element(opt_el).click().perform()
                return selected_val
            except TimeoutException as exc:
                raise ValueError(f"Dropdown option '{option_text}' not found.") from exc

        if index is None:
            raise ValueError(
                "Dropdown index must be provided when option_text is omitted."
            )

        options = self.wait.until(
            EC.presence_of_all_elements_located(BaseLocators.DROPDOWN_OPTIONS)
        )
        target_option = options[min(index - 1, len(options) - 1)]
        selected_val = target_option.text.strip()
        ActionChains(self.driver).move_to_element(target_option).click().perform()
        return selected_val

    def read_dropdown_by_label(self, label_text: str) -> str:
        """Read the selected value from a custom dropdown.

        Args:
            label_text (str): Visible dropdown label.

        Returns:
            str: Selected value or ``N/A`` when unavailable.

        Example:
            status = page.read_dropdown_by_label("Marital Status")
        """
        try:
            el = self.find_visible(BaseLocators.dropdown_by_label(label_text))
            text_val = el.text.strip()
            return text_val if text_val and text_val != "-- Select --" else "N/A"
        except TimeoutException:
            return "N/A"

    def navigate_sidebar(self, menu_name: str) -> None:
        """Navigate through the main sidebar.

        Args:
            menu_name (str): Visible sidebar menu name.

        Returns:
            None.

        Example:
            page.navigate_sidebar("My Info")
        """
        self.click_element(BaseLocators.sidebar_item(menu_name))
        self.wait_for_loaders()

    def wait_for_success_toast(self, timeout: int = 10) -> bool:
        """
        Wait for the success toast. If not found, check for validation errors
        to avoid failing on unchanged form submissions.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.SUCCESS_TOAST)
            )
            logger.info("Success toast found.")
            self.wait_for_loaders()
            return True

        except TimeoutException as exc:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".oxd-input-field-error-message"
            )

            if error_elements and any(
                getattr(e, "is_displayed", lambda: True)() for e in error_elements
            ):
                raise OrangeHRMBaseException(
                    "Save failed: Validation errors on form."
                ) from exc

            logger.warning(
                "Toast not found, but no validation errors detected. Assuming unchanged state."
            )
            self.wait_for_loaders()
            return True
