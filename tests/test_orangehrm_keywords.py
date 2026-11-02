"""Unit tests for the OrangeHRM Robot Framework keyword library."""

import unittest
from unittest.mock import Mock, patch

from selenium.common.exceptions import WebDriverException

from src.exceptions import MyInfoAutomationError
from src.keywords.orangehrm_keywords import OrangeHRMKeywords


class OrangeHRMKeywordsTests(unittest.TestCase):
    def test_phase3_catches_webdriverexception(self) -> None:
        keywords = OrangeHRMKeywords()
        keywords.driver = Mock()
        keywords._capture_failure_state = Mock()

        with patch("src.keywords.orangehrm_keywords.MyInfoPage") as my_info_page_class:
            my_info_page_class.return_value.process_all_ten_sections.side_effect = (
                WebDriverException("driver unavailable")
            )

            with self.assertRaises(MyInfoAutomationError):
                keywords.execute_phase_3_my_info_module()

        keywords._capture_failure_state.assert_called_once_with(
            "phase3_my_info_failure"
        )


if __name__ == "__main__":
    unittest.main()
