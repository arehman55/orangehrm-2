"""
Phase 1: Authentication Page Object Model.
Handles portal login and dashboard verification with custom exceptions.
"""

import logging

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.base_page import BasePage
from src.exceptions import AuthenticationError
from src.pages.locators import LoginLocators

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object for OrangeHRM Login Module."""

    USERNAME_FIELD = LoginLocators.USERNAME_FIELD
    PASSWORD_FIELD = LoginLocators.PASSWORD_FIELD
    LOGIN_BTN = LoginLocators.LOGIN_BUTTON
    DASHBOARD_HEADER = LoginLocators.DASHBOARD_HEADER

    def login(self, base_url: str, username: str, password: str) -> None:
        """Navigate to the portal, authenticate, and verify the dashboard.

        Args:
            base_url (str): Login page URL.
            username (str): Account username.
            password (str): Account password.

        Returns:
            None.

        Example:
            page.login(base_url, "Admin", "********")  # Never hardcode real passwords in docs
        """
        logger.info("Navigating to login portal: %s", base_url)
        self.driver.get(base_url)
        self.wait_for_loaders()

        try:
            logger.info("Entering credentials...")
            self.clear_and_type(self.USERNAME_FIELD, username)
            self.clear_and_type(self.PASSWORD_FIELD, password)
            self.click_element(self.LOGIN_BTN)

            logger.info("Verifying Dashboard arrival...")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(self.DASHBOARD_HEADER)
            )
            logger.info("Authentication successful and Dashboard loaded.")
        except (TimeoutException, WebDriverException, ValueError) as exc:
            raise AuthenticationError(
                f"Failed to authenticate with OrangeHRM portal: {exc}"
            ) from exc
