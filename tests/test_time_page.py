"""Unit tests for the time page."""

import unittest
from unittest.mock import Mock, call

from src.pages.time_page import TimePage


class TimePageTests(unittest.TestCase):
    def test_zero_hours_not_replaced(self) -> None:
        page = TimePage.__new__(TimePage)
        page.driver = Mock()
        page._enter_edit_mode = Mock()
        page._reset_to_single_clean_row = Mock()
        page._click_add_row_plus_button = Mock()
        page._populate_project_and_activity = Mock()
        page._input_hours_for_day = Mock()
        page._save_and_confirm_redirect = Mock()

        zero_hour_input = Mock()
        page.find_all_visible = Mock(return_value=[zero_hour_input] * 8)

        page.enter_and_save_timesheet({"hours": {"Mon": "00:00"}})

        self.assertEqual(page._input_hours_for_day.call_count, 6)
        self.assertNotIn(call(1, 0, "04:00"), page._input_hours_for_day.call_args_list)
        self.assertNotIn(call(1, 0, "00:00"), page._input_hours_for_day.call_args_list)
        zero_hour_input.send_keys.assert_not_called()


if __name__ == "__main__":
    unittest.main()
