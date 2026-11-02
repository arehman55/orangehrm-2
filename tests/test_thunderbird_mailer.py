"""Unit tests for Thunderbird desktop mail dispatch."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from src.services.thunderbird_mailer import ThunderbirdMailer


class ThunderbirdMailerTests(unittest.TestCase):
    def test_build_timesheet_html_escapes_html(self) -> None:
        html_body = ThunderbirdMailer._build_timesheet_html(
            [{"Project": "<script>alert(1)</script>"}], "OrangeHRM2026!"
        )

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_body)
        self.assertNotIn("<script>alert(1)</script>", html_body)

    def test_thunderbird_dispatches_via_locator(self) -> None:
        desktop = Mock()
        window_backend = MagicMock()
        window_backend.__enter__.return_value = window_backend
        window_backend.find_window.return_value = Mock()
        window_backend.is_active.return_value = True
        window_backend.is_open.return_value = False

        with (
            patch("src.services.thunderbird_mailer.Desktop", return_value=desktop),
            patch("src.services.thunderbird_mailer.subprocess.Popen") as popen,
            patch.object(
                ThunderbirdMailer, "_open_window_backend", return_value=window_backend
            ),
            patch("src.services.thunderbird_mailer.COMPOSE_SETTLE_SECONDS", 0),
            patch("src.services.thunderbird_mailer.FOCUS_RETRY_SECONDS", 0),
        ):
            mailer = ThunderbirdMailer()
            mailer._compose_and_dispatch("to='fa22-bcs-260@students.cuisahiwal.edu.pk'")

        popen.assert_called_once()
        window_backend.find_window.assert_called_once_with("Write:")
        window_backend.activate.assert_called_once_with(
            window_backend.find_window.return_value
        )
        desktop.press_keys.assert_called_once_with("ctrl", "enter")


if __name__ == "__main__":
    unittest.main()
