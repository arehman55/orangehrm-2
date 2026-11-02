"""Unit tests for the base page."""

import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from src.base_page import BasePage
from src.exceptions import AttachmentUploadError, OrangeHRMBaseException


class BasePageTests(unittest.TestCase):
    def test_toast_timeout_without_validation_errors_assumes_unchanged(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.driver.find_elements.return_value = []
        page.wait_for_loaders = Mock()

        with patch("src.base_page.WebDriverWait") as wait_class:
            wait_class.return_value.until.side_effect = TimeoutException()

            self.assertTrue(page.wait_for_success_toast())

        page.wait_for_loaders.assert_called_once_with()

    def test_toast_timeout_with_validation_errors_raises(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.driver.find_elements.return_value = [Mock()]
        page.wait_for_loaders = Mock()

        with patch("src.base_page.WebDriverWait") as wait_class:
            wait_class.return_value.until.side_effect = TimeoutException()

            with self.assertRaisesRegex(
                OrangeHRMBaseException,
                "Save failed: Validation errors on form.",
            ):
                page.wait_for_success_toast()

        page.wait_for_loaders.assert_not_called()

    def test_upload_swallow_fixed(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.wait = Mock()
        page.wait_for_loaders = Mock()
        page.wait.until.side_effect = TimeoutException()

        with self.assertRaises(AttachmentUploadError):
            page.upload_attachment_in_current_section(
                Path("attachment.txt"), "Test attachment"
            )

    def test_missing_option_raises(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.click_element = Mock()
        page.wait = Mock()
        page.wait.until.return_value = [Mock(text="First"), Mock(text="Second")]

        with patch("src.base_page.WebDriverWait") as wait_class:
            wait_class.return_value.until.side_effect = TimeoutException()

            with self.assertRaisesRegex(
                ValueError,
                "Dropdown option 'Missing' not found.",
            ):
                page.select_dropdown_by_label("Status", option_text="Missing")

    def test_placeholder_tab_press_strict_match(self) -> None:
        page = BasePage.__new__(BasePage)
        page.driver = Mock()
        page.driver.find_elements.return_value = []
        input_element = Mock()
        page.find_visible = Mock(return_value=input_element)

        action_chain = Mock()
        action_chain.move_to_element.return_value = action_chain
        action_chain.send_keys.return_value = action_chain
        action_chain.click.return_value = action_chain

        with patch("src.base_page.ActionChains", return_value=action_chain):
            input_element.get_attribute.return_value = "Add a comment"
            page.clear_and_type(("id", "comment"), "Updated comment")

            self.assertNotIn(call(Keys.TAB), input_element.send_keys.call_args_list)

            input_element.send_keys.reset_mock()
            input_element.get_attribute.return_value = "yyyy-mm-dd"
            page.clear_and_type(("id", "date"), "2026-10-29")

        input_element.send_keys.assert_any_call(Keys.TAB)


if __name__ == "__main__":
    unittest.main()
