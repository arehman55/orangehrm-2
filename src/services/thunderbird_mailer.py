"""
Phase 4: Mozilla Thunderbird Desktop Email Automation Page Object Model.
Uses Pure Python, RPA.Desktop keyboard control, CLI compose commands and
native window helpers (python-xlib on Linux, ctypes on Windows) so the compose
window is located, focused and verified on both Windows & Ubuntu.
"""

import ctypes
import html
import logging
import os
import platform
import re
import subprocess
import time
from abc import ABC, abstractmethod
from ctypes import wintypes
from pathlib import Path
from typing import Any

import pandas as pd
from RPA.Desktop import Desktop

from src.security import encrypt_excel_with_password

try:  # python-xlib is Linux-only; pynput (used by RPA.Desktop) installs it there.
    from Xlib import X, display, protocol
    from Xlib import error as xlib_error
except ImportError:
    X = display = protocol = xlib_error = None

from src.config import (
    AUTOMATION_AUTHOR,
    EMAIL_1_SUBJECT,
    MY_INFO_SECTIONS,
    OUTPUT_DIR,
    TEAM_LEAD_EMAIL,
    THUNDERBIRD_PATHS,
    format_my_info_section_label,
)
from src.exceptions import EmailAutomationError

logger = logging.getLogger(__name__)

# Fallback window-title marker when the compose argument has no subject.
COMPOSE_TITLE_MARKER = "Write:"

# Thunderbird maps the compose window before the HTML body and the attachment
# finish loading; sending too early silently does nothing.
COMPOSE_SETTLE_SECONDS = 2.0
FOCUS_ATTEMPTS = 3
FOCUS_RETRY_SECONDS = 0.5
POLL_INTERVAL_SECONDS = 0.25
# Thunderbird closes the compose window once the message is handed to SMTP,
# which can take a while with attachments on slow links.
SEND_CONFIRM_SECONDS = 60.0


class _WindowBackend(ABC):
    """Locate, focus and track a top-level window by part of its title.

    Why: RPA.Desktop only offers image/OCR/coordinate locators, so native
    window handling is isolated here, one implementation per operating system.
    """

    def __enter__(self) -> "_WindowBackend":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def close(self) -> None:
        """Release OS resources held by the backend."""

    @abstractmethod
    def find_window(self, title_fragment: str) -> Any:
        """Return a visible window whose title contains the text, else None."""

    @abstractmethod
    def activate(self, window: Any) -> None:
        """Ask the OS to bring the window to the foreground with keyboard focus."""

    @abstractmethod
    def is_active(self, window: Any) -> bool:
        """Return True when the window currently has the focus."""

    @abstractmethod
    def is_open(self, window: Any) -> bool:
        """Return True while the window still exists and is visible."""


class _X11Backend(_WindowBackend):
    """Linux backend built on python-xlib and the EWMH window-manager hints."""

    def __init__(self) -> None:
        if X is None:
            raise EmailAutomationError(
                "Linux window control needs python-xlib; it is normally installed "
                "with RPA.Desktop (pynput). Add 'python-xlib' to conda.yaml if missing."
            )
        try:
            self._display = display.Display()
        except xlib_error.DisplayError as exc:
            raise EmailAutomationError(
                f"Cannot connect to the X11 display '{os.environ.get('DISPLAY')}': {exc}"
            ) from exc
        self._active_atom = self._display.intern_atom("_NET_ACTIVE_WINDOW")
        self._name_atom = self._display.intern_atom("_NET_WM_NAME")
        self._utf8_atom = self._display.intern_atom("UTF8_STRING")

    def close(self) -> None:
        self._display.close()

    def find_window(self, title_fragment: str) -> Any:
        return self._search(self._display.screen().root, title_fragment.lower())

    def activate(self, window: Any) -> None:
        root = self._display.screen().root
        # EWMH request (source=2: pager) - the only way modern window managers
        # accept a focus change from another client without focus-stealing blocks.
        request = protocol.event.ClientMessage(
            window=window,
            client_type=self._active_atom,
            data=(32, [2, X.CurrentTime, 0, 0, 0]),
        )
        root.send_event(
            request,
            event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask,
        )
        # Plain X focus covers minimal window managers that ignore EWMH.
        catcher = xlib_error.CatchError(xlib_error.BadMatch, xlib_error.BadWindow)
        window.set_input_focus(X.RevertToParent, X.CurrentTime, onerror=catcher)
        self._display.sync()
        if catcher.get_error():
            logger.debug(
                "X input focus request was rejected; relying on the EWMH request."
            )

    def is_active(self, window: Any) -> bool:
        root = self._display.screen().root
        prop = root.get_full_property(self._active_atom, X.AnyPropertyType)
        if prop is not None and len(prop.value):
            return prop.value[0] == window.id
        # No EWMH-aware window manager: fall back to the raw X input focus.
        return self._display.get_input_focus().focus == window

    def is_open(self, window: Any) -> bool:
        try:
            return window.get_attributes().map_state == X.IsViewable
        except xlib_error.XError:  # BadWindow: the window was destroyed.
            return False

    def _search(self, window: Any, needle: str) -> Any:
        """Depth-first walk, because window managers wrap clients in frame windows."""
        try:
            if needle in self._title_of(window).lower() and self._is_viewable(window):
                return window
            children = window.query_tree().children
        except xlib_error.XError:  # The window vanished while we were walking.
            return None
        for child in children:
            match = self._search(child, needle)
            if match is not None:
                return match
        return None

    def _title_of(self, window: Any) -> str:
        """Read the UTF-8 EWMH title first, then the legacy WM_NAME."""
        prop = window.get_full_property(self._name_atom, self._utf8_atom)
        if prop is not None and prop.value:
            return self._to_text(prop.value)
        return self._to_text(window.get_wm_name())

    @staticmethod
    def _to_text(value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value if isinstance(value, str) else ""

    @staticmethod
    def _is_viewable(window: Any) -> bool:
        return window.get_attributes().map_state == X.IsViewable


class _Win32Backend(_WindowBackend):
    """Windows backend built on user32 through ctypes (no extra packages)."""

    _SW_RESTORE = 9
    _VK_MENU = 0x12  # Alt key
    _KEYEVENTF_KEYUP = 0x0002

    def __init__(self) -> None:
        # Private DLL instance so our argtypes never leak into other libraries.
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.keybd_event.argtypes = [
            wintypes.BYTE,
            wintypes.BYTE,
            wintypes.DWORD,
            ctypes.c_size_t,
        ]
        self._user32 = user32

    def find_window(self, title_fragment: str) -> Any:
        needle = title_fragment.lower()
        matches: list[int] = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def collect(hwnd: int, _lparam: int) -> bool:
            if (
                self._user32.IsWindowVisible(hwnd)
                and needle in self._title_of(hwnd).lower()
            ):
                matches.append(hwnd)
            return True  # Keep enumerating.

        self._user32.EnumWindows(collect, 0)
        return matches[0] if matches else None

    def activate(self, window: Any) -> None:
        if self._user32.IsIconic(window):
            self._user32.ShowWindow(window, self._SW_RESTORE)
        # Windows refuses SetForegroundWindow from background processes; a
        # synthetic Alt tap marks our process as having recent user input.
        self._user32.keybd_event(self._VK_MENU, 0, 0, 0)
        self._user32.keybd_event(self._VK_MENU, 0, self._KEYEVENTF_KEYUP, 0)
        self._user32.SetForegroundWindow(window)

    def is_active(self, window: Any) -> bool:
        return self._user32.GetForegroundWindow() == window

    def is_open(self, window: Any) -> bool:
        return bool(
            self._user32.IsWindow(window) and self._user32.IsWindowVisible(window)
        )

    def _title_of(self, hwnd: int) -> str:
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value


class ThunderbirdMailer:
    """Service for automating Mozilla Thunderbird with native window control."""

    def __init__(self, timeout: int = 20) -> None:
        """Initialize the desktop adapter and Thunderbird executable.

        Args:
            timeout (int): Maximum compose-window startup wait in seconds.

        Returns:
            None.

        Example:
            mailer = ThunderbirdMailer(timeout=10)
        """
        self.desktop = Desktop()
        self.timeout = timeout
        self.tb_exe = self._resolve_thunderbird_executable()

    def _resolve_thunderbird_executable(self) -> str:
        """Resolve the Thunderbird executable for the current operating system.

        Args:
            None.

        Returns:
            str: Executable command or path.

        Example:
            executable = mailer._resolve_thunderbird_executable()
        """
        current_os = platform.system()

        if current_os == "Linux":
            # On Ubuntu/Linux, Thunderbird is universally accessible via terminal command
            return "thunderbird"

        elif current_os == "Windows":
            for path in THUNDERBIRD_PATHS:
                if path.exists():
                    return str(path)

        raise EmailAutomationError(
            f"Mozilla Thunderbird executable not found for OS: {current_os}"
        )

    def send_timesheet_html_email(self, timesheet_excel_path: Path) -> None:
        """
        Secure the timesheet workbook with a password and send it as an HTML email.

        Args:
            timesheet_excel_path (Path): Timesheet workbook to attach.

        Returns:
            None.

        Raises:
            EmailAutomationError: If the Timesheet Excel file is missing.

        Example:
            mailer.send_timesheet_html_email(Path("output/OrangeHRM_Data.xlsx"))
        """
        if not timesheet_excel_path.exists():
            raise EmailAutomationError(
                f"Timesheet Excel file not found at: {timesheet_excel_path}"
            )

        logger.info(
            "Encrypting Timesheet Excel file with native Office password protection..."
        )

        # 1. Define the simple security password
        simple_password = "OrangeHRM2026!"

        # 2. Encrypt the raw Excel file as a native Office workbook
        encrypted_excel_path = encrypt_excel_with_password(
            timesheet_excel_path, simple_password
        )

        logger.info(
            "Building HTML tabular body from '%s'...", timesheet_excel_path.name
        )
        df = pd.read_excel(timesheet_excel_path)
        records = df.to_dict(orient="records")

        # 3. Build the HTML body, passing the password so it displays in the email
        html_body = self._build_timesheet_html(records, simple_password)

        # 4. Write the HTML body to a temporary file
        temp_html = OUTPUT_DIR / "orangehrm_email1_body.html"
        temp_html.write_text(html_body, encoding="utf-8")

        # 5. Attach the absolute path of the encrypted Excel workbook
        attachment_path = os.path.abspath(encrypted_excel_path)
        safe_team_lead_email = TEAM_LEAD_EMAIL.replace("'", "")
        safe_subject = EMAIL_1_SUBJECT.replace("'", "")

        # 6. Construct the compose argument string for Thunderbird
        compose_arg = (
            f"to='{safe_team_lead_email}',"
            f"subject='{safe_subject}',"
            f"format='html',"
            f"message='{temp_html.resolve()}',"
            f"attachment='{attachment_path}'"
        )

        logger.info(
            "Launching Thunderbird Compose window for Email 1 (Secure Timesheet)..."
        )
        self._compose_and_dispatch(compose_arg)
        logger.info("Email 1 (Secure Timesheet HTML Report) dispatched successfully.")

    def send_reply_with_details_excel(self, details_excel_path: Path) -> None:
        """
        Secure the details workbook with a password and send it as a threaded reply.

        Args:
            details_excel_path (Path): Path to the generated Details workbook.

        Returns:
            None.

        Raises:
            EmailAutomationError: If the Details Excel file is missing.

        Example:
            mailer.send_reply_with_details_excel(Path("output/Details.xlsx"))
        """
        if not details_excel_path.exists():
            raise EmailAutomationError(
                f"Details Excel file not found at: {details_excel_path}"
            )

        logger.info("Encrypting Details.xlsx with native Office password protection...")

        # 1. Define the simple security password
        simple_password = "OrangeHRM2026!"

        # 2. Encrypt the raw Excel file as a native Office workbook
        encrypted_excel_path = encrypt_excel_with_password(
            details_excel_path, simple_password
        )

        logger.info("Preparing Email 2 (Reply with encrypted Excel attached)...")

        # 3. Build the HTML body, passing the password so it is displayed in the email
        reply_html = self._build_details_reply_html(simple_password)

        # 4. Write the HTML body to a temporary file for Thunderbird to consume
        temp_reply_html = OUTPUT_DIR / "orangehrm_email2_reply.html"
        temp_reply_html.write_text(reply_html, encoding="utf-8")

        # 5. Prepend 'Re:' to visually thread the message in the recipient's inbox
        safe_team_lead_email = TEAM_LEAD_EMAIL.replace("'", "")
        safe_subject = EMAIL_1_SUBJECT.replace("'", "")
        reply_subject = f"Re: {safe_subject}"

        # 6. Use the absolute path of the encrypted Excel workbook
        attachment_path = os.path.abspath(encrypted_excel_path)

        # 7. Construct the compose argument string for Thunderbird
        compose_arg = (
            f"to='{safe_team_lead_email}',"
            f"subject='{reply_subject}',"
            f"format='html',"
            f"message='{temp_reply_html.resolve()}',"
            f"attachment='{attachment_path}'"
        )

        logger.info(
            "Launching Thunderbird Compose window for Email 2 (Secure Reply)..."
        )
        self._compose_and_dispatch(compose_arg)
        logger.info(
            "Email 2 (Reply with encrypted Details.xlsx) dispatched successfully."
        )

    def _compose_and_dispatch(self, compose_arg: str) -> None:
        """
        Open a Thunderbird compose window, send it and confirm it was sent.

        Args:
            compose_arg (str): Thunderbird compose argument string.

        Returns:
            None.
        """
        try:
            process = subprocess.Popen(
                [self.tb_exe, "-compose", compose_arg],
                env=self._build_launch_env(),
            )
            self._send_compose_window(self._extract_subject(compose_arg), process)
            logger.info("Email dispatch sequence completed.")
        except EmailAutomationError:
            raise
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            raise EmailAutomationError(
                f"Failed during Thunderbird email dispatch: {exc}"
            ) from exc

    @staticmethod
    def _build_launch_env() -> dict[str, str]:
        """Return a clean environment so Thunderbird ignores Conda/Snap/Wayland leftovers."""
        clean_env = os.environ.copy()
        for key in [
            "LD_LIBRARY_PATH",
            "LD_PRELOAD",
            "PYTHONPATH",
            "PYTHONHOME",
            "GIO_MODULE_DIR",
            "GIO_LAUNCHED_DESKTOP_FILE",
            "GIO_LAUNCHED_DESKTOP_FILE_PID",
            "GTK_PATH",
            "GTK_EXE_PREFIX",
            "GTK_IM_MODULE_FILE",
            "WAYLAND_DISPLAY",
        ]:
            clean_env.pop(key, None)

        if platform.system() == "Linux":
            clean_env["GDK_BACKEND"] = "x11"
            clean_env["MOZ_ENABLE_WAYLAND"] = "0"
            clean_env.setdefault("DISPLAY", ":0")
        return clean_env

    @staticmethod
    def _extract_subject(compose_arg: str) -> str:
        """Return the subject from the compose argument, or '' when absent.

        Why: the subject is language-independent, unlike the "Write:" prefix,
        and it tells our compose window apart from any other Thunderbird window.
        """
        match = re.search(r"subject='([^']*)'", compose_arg)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _open_window_backend() -> _WindowBackend:
        """Return the native window helper for the current operating system."""
        current_os = platform.system()
        if current_os == "Linux":
            return _X11Backend()
        if current_os == "Windows":
            return _Win32Backend()
        raise EmailAutomationError(
            f"Thunderbird window control is not supported on OS: {current_os}"
        )

    def _send_compose_window(self, subject: str, process: subprocess.Popen) -> None:
        """Wait for the compose window, focus it, press Ctrl+Enter and confirm it closed."""
        title_fragment = subject or COMPOSE_TITLE_MARKER
        with self._open_window_backend() as windows:
            window = self._wait_for_compose_window(windows, title_fragment, process)
            logger.info(
                "Compose window detected; letting the body and attachment load..."
            )
            time.sleep(COMPOSE_SETTLE_SECONDS)

            self._focus_window(windows, window)
            logger.info("Dispatching email with Ctrl+Enter...")
            self.desktop.press_keys("ctrl", "enter")
            self._wait_for_window_closed(windows, window)

    def _wait_for_compose_window(
        self, windows: _WindowBackend, title_fragment: str, process: subprocess.Popen
    ) -> Any:
        """Poll until the compose window is visible or the startup timeout expires."""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            window = windows.find_window(title_fragment)
            if window is not None:
                return window

            # Exit code 0 is normal: Thunderbird hands the request to an already
            # running instance. Anything else means it crashed on startup, so
            # fail now with the real cause instead of waiting out the timeout.
            exit_code = process.poll()
            if isinstance(exit_code, int) and exit_code != 0:
                raise EmailAutomationError(
                    f"Thunderbird exited with code {exit_code} before the compose "
                    "window appeared. Its error is printed in the terminal above; "
                    "launching the bot from an IDE terminal (e.g. snap VS Code) can "
                    "leak libraries that break Thunderbird."
                )
            time.sleep(POLL_INTERVAL_SECONDS)

        raise EmailAutomationError(
            f"Thunderbird compose window '{title_fragment}' was not found within "
            f"{self.timeout}s. Check that Thunderbird has a configured mail account "
            "and, on Linux, that it runs under X11/XWayland: close any already "
            "running Thunderbird so this bot starts it with the X11 environment."
        )

    @staticmethod
    def _focus_window(windows: _WindowBackend, window: Any) -> None:
        """Re-request focus until the OS confirms it, so the keystroke hits the compose window."""
        for _ in range(FOCUS_ATTEMPTS):
            windows.activate(window)
            time.sleep(FOCUS_RETRY_SECONDS)
            if windows.is_active(window):
                return
        # Some desktops do not report focus reliably; the closing check below
        # remains the authoritative proof that the email was sent.
        logger.warning(
            "Focus on the compose window could not be confirmed; sending anyway."
        )

    @staticmethod
    def _wait_for_window_closed(windows: _WindowBackend, window: Any) -> None:
        """Thunderbird closes the compose window itself after a successful send."""
        deadline = time.monotonic() + SEND_CONFIRM_SECONDS
        while time.monotonic() < deadline:
            if not windows.is_open(window):
                return
            time.sleep(POLL_INTERVAL_SECONDS)

        raise EmailAutomationError(
            f"Compose window is still open {SEND_CONFIRM_SECONDS:.0f}s after sending, so "
            "the email is NOT confirmed as sent. Look for an SMTP password prompt, "
            "offline mode or a send error dialog in Thunderbird."
        )

    @staticmethod
    def _build_timesheet_html(
        records: list[dict[str, Any]], simple_password: str
    ) -> str:
        """Build an HTML table for timesheet records, including workbook password instructions.

        Args:
            records (list[dict[str, Any]]): Timesheet rows.
            simple_password (str): The password required to unlock the attached workbook.

        Returns:
            str: Rendered HTML email body.

        Example:
            html = ThunderbirdMailer._build_timesheet_html(records, "OrangeHRM2026!")
        """
        if not records:
            return "<p>No timesheet records available.</p>"

        headers = list(records[0].keys())
        header_cells_html = "".join(
            f"<th style='background-color:#F2F2F2; color:#000000; padding:8px 10px; "
            f"border:1px solid #CCCCCC; text-align:center; font-family:Calibri,sans-serif; font-size:12px; font-weight:bold;'>{h}</th>"
            for h in headers
        )

        rows_html = ""
        for idx, row in enumerate(records):
            bg_color = "#F9F9F9" if idx % 2 == 1 else "#FFFFFF"
            row_cells = ""
            active_day_label = "N/A"

            for col_name in headers:
                val_str = str(row.get(col_name, "")).strip()
                if col_name not in (
                    "Entry_No",
                    "Project",
                    "Activity",
                    "Total",
                ) and val_str not in ("00:00", "0", "", "N/A"):
                    active_day_label = col_name

            for col_name in headers:
                val_str = str(row.get(col_name, "00:00")).strip()

                if col_name == "Project":
                    cell_style = f"background-color:{bg_color}; color:#000000; font-weight:bold; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == "Activity":
                    cell_style = f"background-color:{bg_color}; color:#333333; font-weight:normal; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == active_day_label:
                    cell_style = "background-color:#EAEAEA; color:#000000; font-weight:bold; text-align:center; padding:8px 10px; border:1.5px solid #000000;"
                    val_str = f"{val_str} *"
                else:
                    cell_style = f"background-color:{bg_color}; color:#555555; text-align:center; padding:8px 10px; border:1px solid #CCCCCC;"

                row_cells += f"<td style='{cell_style}'>{html.escape(val_str)}</td>"

            rows_html += f"<tr>{row_cells}</tr>"

        return f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; color: #111111; line-height: 1.5; font-size: 13px;">
            <p>Dear Team Lead,</p>
            <p>The automated RPA bot has successfully executed the 7-day timesheet entries on the OrangeHRM portal. Below is the tabular summary of the weekly activities:</p>
            
            <p><strong>SECURITY INSTRUCTION:</strong><br>
            The attached <strong>OrangeHRM_Data_protected.xlsx</strong> workbook is encrypted with an open password. Please use the password below to open it:<br>
            <em>(Note for Mobile Users: Open the workbook in an Excel-compatible viewer and enter the password when prompted.)</em></p>
            
            <p style="padding: 10px; background-color: #f8f9fa; border-left: 4px solid #007bff; font-family: monospace; font-size: 14px; margin: 10px 0;">
                <strong>{html.escape(simple_password)}</strong>
            </p>
            
            <table style="border-collapse: collapse; width: 100%; margin-top: 15px; margin-bottom: 15px; font-size: 12px;">
                <thead>
                    <tr>{header_cells_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <p>The encrypted Excel workbook is attached to this email. A follow-up reply containing the complete 10-section My Info Details workbook will follow shortly.</p>
            <p style="margin-top: 20px;">Best regards,<br><strong>{html.escape(AUTOMATION_AUTHOR)}</strong><br><em>Enterprise RPA Automation Suite</em></p>
        </body>
        </html>
        """

    @staticmethod
    def _build_details_reply_html(simple_password: str) -> str:
        """Build the HTML body for the details workbook reply, including security instructions.

        Args:
            simple_password (str): The password required to unlock the attached workbook.

        Returns:
            str: Rendered HTML email body.

        Example:
            html = ThunderbirdMailer._build_details_reply_html("OrangeHRM2026!")
        """
        sections = [
            (
                format_my_info_section_label(section_name, position),
                "Completed + Attachments Block"
                if position in (6, 7, 8)
                else "Completed + PDF Hyperlink",
            )
            for position, section_name in enumerate(MY_INFO_SECTIONS, start=1)
        ]

        rows_html = "".join(
            f"<tr>"
            f"<td style='padding:7px 10px; border:1px solid #CCCCCC; font-weight:bold; color:#000000;'>{html.escape(sec)}</td>"
            f"<td style='padding:7px 10px; border:1px solid #CCCCCC; color:#333333; background-color:#FAFAFA;'>{html.escape(status)}</td>"
            f"</tr>"
            for sec, status in sections
        )

        return f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; color: #111111; line-height: 1.5; font-size: 13px;">
            <p>Dear Team Lead,</p>
            <p>In continuation of the previous report, please find attached the consolidated <strong>Details_protected.xlsx</strong> workbook generated from Phase 3 (My Info Module).</p>
            
            <p><strong>SECURITY INSTRUCTION:</strong><br>
            The attached Excel workbook is password-protected. Please use the password below to open the file:</p>
            
            <p style="padding: 10px; background-color: #f8f9fa; border-left: 4px solid #007bff; font-family: monospace; font-size: 14px; margin: 10px 0;">
                <strong>{html.escape(simple_password)}</strong>
            </p>

            <p>Each worksheet contains primary records followed by an ATTACHMENTS block with clickable local PDF hyperlinks:</p>

            <table style="border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 12px;">
                <thead>
                    <tr>
                        <th style="background-color:#F2F2F2; color:#000000; padding:8px 10px; border:1px solid #CCCCCC; text-align:left;">Worksheet / Section</th>
                        <th style="background-color:#F2F2F2; color:#000000; padding:8px 10px; border:1px solid #CCCCCC; text-align:left;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <p>Best regards,<br><strong>{html.escape(AUTOMATION_AUTHOR)}</strong><br><em>Enterprise RPA Automation Suite</em></p>
        </body>
        </html>
        """
