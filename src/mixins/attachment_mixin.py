"""
Mixin providing attachment upload and metadata scraping capabilities
for OrangeHRM Page Objects.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.exceptions import AttachmentUploadError, OrangeHRMBaseException
from src.pages.locators import BaseLocators, MyInfoLocators

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


class AttachmentMixin:
    """Handles PDF attachment uploads and table scraping across OrangeHRM sections."""

    driver: WebDriver

    ATTACHMENT_ADD_BTN = (
        By.XPATH,
        "//h6[normalize-space()='Attachments']/ancestor::div[contains(@class,'orangehrm-action-header')]//button[contains(.,'Add')]",
    )
    FILE_INPUT = (By.XPATH, "//input[@type='file']")
    ATTACHMENT_COMMENT_INPUT = (
        By.XPATH,
        "//h6[normalize-space()='Add Attachment']/ancestor::div[contains(@class,'orangehrm-card-container')]//textarea",
    )
    ATTACHMENT_SAVE_BTN = (
        By.XPATH,
        "//h6[normalize-space()='Add Attachment']/ancestor::div[contains(@class,'orangehrm-card-container')]//button[@type='submit']",
    )
    ATTACHMENT_TABLE_ROWS = (
        By.XPATH,
        "//h6[normalize-space()='Attachments']/ancestor::div[contains(@class,'orangehrm-container') or contains(@class,'orangehrm-paper-container') or contains(@class,'orangehrm-horizontal-padding')]/following-sibling::div//div[@class='oxd-table-body']//div[@role='row']",
    )

    def _wait_for_previous_toast_to_clear(self) -> None:
        """Ensure any existing toast notification disappears before starting a new action."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(BaseLocators.SUCCESS_TOAST)
            )
        except TimeoutException:
            pass

    def upload_attachment_in_current_section(
        self, file_path: Path, comment: str
    ) -> None:
        """
        Upload a file attachment in the active section and validate completion.

        Args:
            file_path (Path): Path to the file to upload.
            comment (str): Description comment for the attachment.

        Raises:
            AttachmentUploadError: If the file is missing or the upload fails.
        """
        resolved_path = Path(file_path).resolve()
        if not resolved_path.is_file():
            raise AttachmentUploadError(
                f"Attachment file does not exist: {resolved_path}"
            )

        wait = WebDriverWait(self.driver, getattr(self, "timeout", 20))

        try:
            self.wait_for_loaders()  # type: ignore[attr-defined]
            self._wait_for_previous_toast_to_clear()

            # 1. Click '+ Add' inside the Attachments section
            add_locator = getattr(
                MyInfoLocators, "ATTACHMENT_ADD_BUTTON", self.ATTACHMENT_ADD_BTN
            )
            add_btn = wait.until(EC.element_to_be_clickable(add_locator))
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", add_btn
            )
            self.click_element(add_locator)  # type: ignore[attr-defined]

            # 2. Send file path to the hidden <input type="file">
            file_input_locator = getattr(MyInfoLocators, "FILE_INPUT", self.FILE_INPUT)
            file_input = wait.until(EC.presence_of_element_located(file_input_locator))
            file_input.send_keys(str(resolved_path))

            # 3. Enter attachment comment
            comment_locator = getattr(
                MyInfoLocators,
                "ATTACHMENT_COMMENT_INPUT",
                self.ATTACHMENT_COMMENT_INPUT,
            )
            comment_box = wait.until(EC.visibility_of_element_located(comment_locator))
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", comment_box
            )
            comment_box.clear()
            comment_box.send_keys(comment)

            # 4. Click the 'Save' button inside the 'Add Attachment' container
            save_locator = getattr(
                MyInfoLocators, "ATTACHMENT_SAVE_BUTTON", self.ATTACHMENT_SAVE_BTN
            )
            save_btn = wait.until(EC.element_to_be_clickable(save_locator))
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", save_btn
            )
            self.click_element(save_locator)  # type: ignore[attr-defined]

            # 5. Validate upload completion
            self.wait_for_success_toast()  # type: ignore[attr-defined]
            self.wait_for_loaders()  # type: ignore[attr-defined]
            logger.info(
                "Successfully uploaded attachment '%s' with comment '%s'.",
                resolved_path.name,
                comment,
            )

        except (TimeoutException, WebDriverException, OrangeHRMBaseException) as exc:
            raise AttachmentUploadError(
                f"Failed to upload attachment '{resolved_path.name}': {exc}"
            ) from exc

    def _try_upload_attachment(self, file_path: Path, comment: str) -> None:
        """Upload an attachment if the current section supports attachments."""
        self.wait_for_loaders()  # type: ignore[attr-defined]
        add_locator = getattr(
            MyInfoLocators, "ATTACHMENT_ADD_BUTTON", self.ATTACHMENT_ADD_BTN
        )
        if self.driver.find_elements(*add_locator):
            self.upload_attachment_in_current_section(file_path, comment)
        else:
            logger.info(
                "No Attachments section present on current tab; skipping upload."
            )

    def capture_attachment_metadata_from_current_section(
        self, section_name: str
    ) -> dict[str, Any]:
        """
        Scrape the first attachment row metadata from the current section's attachment table.
        """
        default_row = {
            "File Name": "N/A",
            "Description": "N/A",
            "Size": "N/A",
            "Type": "N/A",
            "Date Added": "N/A",
            "Added By": "N/A",
            "Download_Status": "No Attachment Found",
        }

        self.wait_for_loaders()  # type: ignore[attr-defined]
        row_locator = getattr(
            MyInfoLocators,
            "ATTACHMENT_TABLE_ROWS",
            getattr(MyInfoLocators, "ATTACHMENT_ROW", self.ATTACHMENT_TABLE_ROWS),
        )

        try:
            rows = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located(row_locator)
            )
            for row in rows:
                cells = row.find_elements(*MyInfoLocators.ATTACHMENT_CELL)
                if len(cells) >= 7:
                    return {
                        "File Name": cells[1].text.strip(),
                        "Description": cells[2].text.strip(),
                        "Size": cells[3].text.strip(),
                        "Type": cells[4].text.strip(),
                        "Date Added": cells[5].text.strip(),
                        "Added By": cells[6].text.strip(),
                        "Download_Status": "Success",
                    }
        except TimeoutException:
            logger.warning(
                "Attachment table lookup timed out in section '%s'.",
                section_name,
            )
        except WebDriverException as exc:
            logger.error(
                "WebDriver failure while capturing attachment metadata in '%s': %s",
                section_name,
                exc,
            )

        return default_row
