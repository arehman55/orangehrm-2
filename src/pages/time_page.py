"""
Phase 2: 'Time' Module Automation & Scraping Page Object Model.
Handles the exact OrangeHRM workflow using 100% Pure Python Selenium (ActionChains)
without any JavaScript injections:
1. Click Edit on /viewMyTimesheet
2. Click the '+' button next to 'Add Row' for each subsequent day (Mon -> Sun, 7 separate saves)
3. Select unique Project & Activity per row
4. Enter hours only for the target day column
5. Click Save -> Wait for redirect back to /viewMyTimesheet -> Validate Edit button
6. Scrape all 7 saved rows into structured Excel format.
"""

import logging
from typing import Any

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.base_page import BasePage
from src.exceptions import TimesheetAutomationError
from src.pages.locators import TimeLocators

logger = logging.getLogger(__name__)


class TimePage(BasePage):
    """Page Object for OrangeHRM Time & My Timesheets module using pure Python Selenium."""

    TIMESHEETS_TOP_MENU = TimeLocators.TIMESHEETS_TOP_MENU
    MY_TIMESHEETS_OPTION = TimeLocators.MY_TIMESHEETS_OPTION
    EDIT_BUTTON = TimeLocators.EDIT_BUTTON
    CREATE_TIMESHEET_BUTTON = TimeLocators.CREATE_TIMESHEET_BUTTON
    SAVE_TIMESHEET_BUTTON = TimeLocators.SAVE_TIMESHEET_BUTTON
    EDITABLE_DATA_ROWS = TimeLocators.EDITABLE_DATA_ROWS
    ADD_ROW_PLUS_BUTTON = TimeLocators.ADD_ROW_PLUS_BUTTON
    DELETE_ROW_BUTTONS = TimeLocators.DELETE_ROW_BUTTONS
    AUTOCOMPLETE_VALID_OPTIONS = TimeLocators.AUTOCOMPLETE_VALID_OPTIONS
    ACTIVITY_VALID_OPTIONS = TimeLocators.ACTIVITY_VALID_OPTIONS
    SAVED_TABLE_HEADERS = TimeLocators.SAVED_TABLE_HEADERS
    SAVED_TABLE_ROWS = TimeLocators.SAVED_TABLE_ROWS

    def navigate_to_my_timesheets(self) -> None:
        """Open the My Timesheets view and ensure it is ready.

        Args:
            None.

        Returns:
            None.

        Example:
            page.navigate_to_my_timesheets()
        """
        logger.info("Navigating to Time -> Timesheets -> My Timesheets...")
        try:
            self.navigate_sidebar("Time")
            self.click_element(self.TIMESHEETS_TOP_MENU)
            self.click_element(self.MY_TIMESHEETS_OPTION)
            self.wait_for_loaders()

            # If timesheet is not yet created for the current week, click 'Create Timesheet'
            try:
                create_btn = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable(self.CREATE_TIMESHEET_BUTTON)
                )
                logger.info("Clicking 'Create Timesheet' for current period...")
                ActionChains(self.driver).move_to_element(create_btn).click().perform()
                self.wait_for_loaders()
            except TimeoutException:
                logger.info("No new timesheet was required for the current period.")

            # Ensure the 'Edit' button is visible on /viewMyTimesheet
            self.find_visible(self.EDIT_BUTTON)
            logger.info(
                "Successfully loaded My Timesheets view (%s).", self.driver.current_url
            )
        except (
            IndexError,
            StaleElementReferenceException,
            TimeoutException,
            ValueError,
            WebDriverException,
        ) as exc:
            raise TimesheetAutomationError(
                f"Failed to navigate to My Timesheets: {exc}"
            ) from exc

    def enter_and_save_timesheet(self, timesheet_data: dict[str, Any]) -> None:
        """
        Enter and save one timesheet row for each day of the week.

        Args:
            timesheet_data (Dict[str, Any]): Timesheet values keyed by day.

        Returns:
            None.

        Example:
            page.enter_and_save_timesheet({"hours": {"Mon": "08:00"}})
        """
        days_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours_map = timesheet_data.get("hours", {})
        used_pairs: set[tuple[str, str]] = set()

        for day_idx, day_name in enumerate(days_order):
            row_num = day_idx + 1
            hour_val = hours_map.get(day_name, "08:00")
            if hour_val in ("00:00", "0", ""):
                logger.info("Skipping zero-hour entry.")
                continue

            logger.info(
                "========== [Timesheet Entry %d/7 | Day: %s | Hours: %s] ==========",
                row_num,
                day_name,
                hour_val,
            )

            try:
                # STEP 1: Click 'Edit' on /viewMyTimesheet to enter Edit mode
                self._enter_edit_mode()

                # STEP 2: Prepare the target row
                if day_idx == 0:
                    self._reset_to_single_clean_row()
                else:
                    self._click_add_row_plus_button(expected_data_rows=row_num)

                # STEP 3: Select a unique Project + Activity in the target data row
                self._populate_project_and_activity(row_num, used_pairs)

                # STEP 4: Enter hours ONLY in the current day's column
                self._input_hours_for_day(row_num, day_idx, hour_val)

                # STEP 5: Click Save and validate redirect back to /viewMyTimesheet
                self._save_and_confirm_redirect(row_num, day_name)

            except (
                IndexError,
                StaleElementReferenceException,
                TimeoutException,
                ValueError,
                WebDriverException,
            ) as exc:
                logger.error(
                    "Failed during Timesheet Entry %d (%s) at URL '%s': %s",
                    row_num,
                    day_name,
                    self.driver.current_url,
                    exc,
                )
                raise TimesheetAutomationError(
                    f"Timesheet Entry {row_num} ({day_name}) failed: {exc}"
                ) from exc

        logger.info(
            "Successfully completed and validated all 7 separate daily Timesheet entries!"
        )

    def _enter_edit_mode(self) -> None:
        """
        Enter timesheet edit mode.

        Args:
            None.

        Returns:
            None.

        Example:
            page._enter_edit_mode()
        """
        self.wait_for_loaders()
        edit_btn = self.wait.until(EC.element_to_be_clickable(self.EDIT_BUTTON))
        try:
            ActionChains(self.driver).move_to_element(edit_btn).click().perform()
        except ElementClickInterceptedException:
            self.wait_for_loaders()
            ActionChains(self.driver).move_to_element(edit_btn).click().perform()

        self.wait_for_loaders()
        self.wait.until(EC.visibility_of_element_located(self.SAVE_TIMESHEET_BUTTON))
        self.wait.until(EC.presence_of_element_located(self.ADD_ROW_PLUS_BUTTON))

    def _reset_to_single_clean_row(self) -> None:
        """Delete existing rows and ensure one editable row remains.

        Args:
            None.

        Returns:
            None.

        Example:
            page._reset_to_single_clean_row()
        """
        self.wait_for_loaders()
        delete_btns = self.driver.find_elements(*self.DELETE_ROW_BUTTONS)
        if delete_btns:
            logger.info(
                "Clearing %d pre-existing timesheet data row(s)...", len(delete_btns)
            )
            for _ in range(len(delete_btns)):
                current_del_btns = self.driver.find_elements(*self.DELETE_ROW_BUTTONS)
                if not current_del_btns:
                    break
                try:
                    ActionChains(self.driver).move_to_element(
                        current_del_btns[0]
                    ).click().perform()
                    self.wait_for_loaders()
                except StaleElementReferenceException:
                    continue

        data_rows = self.driver.find_elements(*self.EDITABLE_DATA_ROWS)
        if len(data_rows) == 0:
            self._click_add_row_plus_button(expected_data_rows=1)

    def _click_add_row_plus_button(self, expected_data_rows: int) -> None:
        """Add rows until the expected data-row count is reached.

        Args:
            expected_data_rows (int): Required number of editable rows.

        Returns:
            None.

        Example:
            page._click_add_row_plus_button(expected_data_rows=2)
        """
        self.wait_for_loaders()
        current_data_rows = len(self.driver.find_elements(*self.EDITABLE_DATA_ROWS))

        while current_data_rows < expected_data_rows:
            logger.info(
                "Clicking '+' (Add Row) button (current data rows: %d -> target: %d)...",
                current_data_rows,
                expected_data_rows,
            )
            plus_btn = self.wait.until(
                EC.element_to_be_clickable(self.ADD_ROW_PLUS_BUTTON)
            )
            try:
                ActionChains(self.driver).move_to_element(plus_btn).click().perform()
            except ElementClickInterceptedException:
                ActionChains(self.driver).move_to_element(plus_btn).click().perform()

            WebDriverWait(self.driver, 10).until(
                lambda d: (
                    len(d.find_elements(*self.EDITABLE_DATA_ROWS)) > current_data_rows
                )
            )
            self.wait_for_loaders()
            current_data_rows = len(self.driver.find_elements(*self.EDITABLE_DATA_ROWS))

    def _populate_project_and_activity(
        self, row_num: int, used_pairs: set[tuple[str, str]]
    ) -> None:
        """Select a unique project and activity for a timesheet row.

        Args:
            row_num (int): One-based timesheet row number.
            used_pairs (Set[Tuple[str, str]]): Previously selected pairs.

        Returns:
            None.

        Example:
            page._populate_project_and_activity(1, set())
        """
        proj_input_locator = TimeLocators.project_input(row_num)
        act_dropdown_locator = TimeLocators.activity_dropdown(row_num)

        search_hints = ["a", "e", "o", "i", "u", "c"]

        for hint in search_hints:
            self._type_project_hint(proj_input_locator, hint)

            try:
                WebDriverWait(self.driver, 6).until(
                    EC.visibility_of_all_elements_located(
                        self.AUTOCOMPLETE_VALID_OPTIONS
                    )
                )
            except TimeoutException:
                continue

            total_projects = len(
                self.driver.find_elements(*self.AUTOCOMPLETE_VALID_OPTIONS)
            )

            for p_idx in range(total_projects):
                if p_idx > 0:
                    self._type_project_hint(proj_input_locator, hint)
                    try:
                        WebDriverWait(self.driver, 6).until(
                            EC.visibility_of_all_elements_located(
                                self.AUTOCOMPLETE_VALID_OPTIONS
                            )
                        )
                    except TimeoutException:
                        break

                proj_els = self.driver.find_elements(*self.AUTOCOMPLETE_VALID_OPTIONS)
                if p_idx >= len(proj_els):
                    break

                proj_el = proj_els[p_idx]
                proj_name = proj_el.text.strip()
                ActionChains(self.driver).move_to_element(proj_el).click().perform()

                self.wait_for_loaders()
                self.click_element(act_dropdown_locator)
                try:
                    WebDriverWait(self.driver, 6).until(
                        EC.visibility_of_all_elements_located(
                            self.ACTIVITY_VALID_OPTIONS
                        )
                    )
                except TimeoutException:
                    continue

                act_els = self.driver.find_elements(*self.ACTIVITY_VALID_OPTIONS)
                for act_el in act_els:
                    act_name = act_el.text.strip()
                    if (proj_name, act_name) not in used_pairs:
                        ActionChains(self.driver).move_to_element(
                            act_el
                        ).click().perform()
                        used_pairs.add((proj_name, act_name))
                        self.wait_for_loaders()
                        logger.info(
                            "Row %d -> Selected Project: '%s' | Activity: '%s'",
                            row_num,
                            proj_name,
                            act_name,
                        )
                        return

                self.click_element(act_dropdown_locator)

        raise TimesheetAutomationError(
            f"Exhausted project suggestions without finding a unique Project+Activity for Row {row_num}."
        )

    def _type_project_hint(self, locator: tuple[str, str], hint: str) -> None:
        """Replace the project search value with a hint.

        Args:
            locator (Tuple[str, str]): Project input locator.
            hint (str): Search text.

        Returns:
            None.

        Example:
            page._type_project_hint(locator, "a")
        """
        proj_input = self.find_visible(locator)
        ActionChains(self.driver).move_to_element(proj_input).perform()
        proj_input.click()
        # Note: Uses CONTROL for Windows/Linux. For macOS support, requires COMMAND.
        proj_input.send_keys(Keys.CONTROL + "a")
        proj_input.send_keys(Keys.BACKSPACE)
        proj_input.send_keys(hint)

    def _input_hours_for_day(self, row_num: int, day_idx: int, hour_val: str) -> None:
        """Enter hours into a target day column.

        Args:
            row_num (int): One-based timesheet row number.
            day_idx (int): Zero-based day column index.
            hour_val (str): Hours value to enter.

        Returns:
            None.

        Example:
            page._input_hours_for_day(1, 0, "08:00")
        """
        all_inputs = self.find_all_visible(TimeLocators.row_inputs(row_num))
        if len(all_inputs) < 8:
            raise TimesheetAutomationError(
                f"Expected at least 8 inputs in Row {row_num}, found {len(all_inputs)}."
            )

        day_inputs = all_inputs[-7:]
        target_day_input = day_inputs[day_idx]

        ActionChains(self.driver).move_to_element(target_day_input).perform()
        target_day_input.click()
        # Note: Uses CONTROL for Windows/Linux. For macOS support, requires COMMAND.
        target_day_input.send_keys(Keys.CONTROL + "a")
        target_day_input.send_keys(Keys.BACKSPACE)
        target_day_input.send_keys(hour_val)
        target_day_input.send_keys(Keys.TAB)

    def _save_and_confirm_redirect(self, row_num: int, day_name: str) -> None:
        """Save a row and confirm the timesheet view is restored.

        Args:
            row_num (int): One-based timesheet row number.
            day_name (str): Day label used in diagnostics.

        Returns:
            None.

        Example:
            page._save_and_confirm_redirect(1, "Mon")
        """
        logger.info("Clicking 'Save' for Row %d (%s)...", row_num, day_name)
        save_btn = self.wait.until(
            EC.element_to_be_clickable(self.SAVE_TIMESHEET_BUTTON)
        )
        try:
            ActionChains(self.driver).move_to_element(save_btn).click().perform()
        except ElementClickInterceptedException:
            ActionChains(self.driver).move_to_element(save_btn).click().perform()

        try:
            WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.visibility_of_element_located(self.EDIT_BUTTON),
                    EC.visibility_of_element_located(TimeLocators.INPUT_ERROR),
                )
            )
        except TimeoutException as exc:
            raise TimesheetAutomationError(
                f"Timed out waiting for page redirect after saving Row {row_num} ({day_name})."
            ) from exc

        inline_errors = self.driver.find_elements(*TimeLocators.INPUT_ERROR)
        if inline_errors:
            err_texts = [e.text.strip() for e in inline_errors if e.text.strip()]
            if err_texts:
                raise TimesheetAutomationError(
                    f"OrangeHRM rejected Timesheet Save on Row {row_num} ({day_name}) with UI error: {err_texts}"
                )

        self.wait_for_loaders()
        self.wait.until(EC.element_to_be_clickable(self.EDIT_BUTTON))
        logger.info("Validated Row %d (%s) saved successfully!", row_num, day_name)

    def scrape_saved_timesheet(self) -> list[dict[str, Any]]:
        """Scrape the final read-only timesheet table.

        Args:
            None.

        Returns:
            List[Dict[str, Any]]: Saved timesheet rows.

        Example:
            rows = page.scrape_saved_timesheet()
        """
        self.wait_for_loaders()
        self.find_visible(self.EDIT_BUTTON)

        headers_els = self.find_all_visible(self.SAVED_TABLE_HEADERS)
        clean_headers = [
            " ".join(h.text.strip().split()) or f"Column_{i}"
            for i, h in enumerate(headers_els)
        ]

        rows_els = self.find_all_visible(self.SAVED_TABLE_ROWS)
        scraped_data: list[dict[str, Any]] = []

        for row_idx, row in enumerate(rows_els, start=1):
            cells = row.find_elements(*TimeLocators.TABLE_CELL)
            row_dict: dict[str, Any] = {"Entry_No": row_idx}
            for col_idx, cell in enumerate(cells):
                header_name = (
                    clean_headers[col_idx]
                    if col_idx < len(clean_headers)
                    else f"Col_{col_idx}"
                )
                val = cell.text.strip()
                row_dict[header_name] = val if val else "00:00"
            scraped_data.append(row_dict)

        logger.info(
            "Scraped %d saved timesheet rows from /viewMyTimesheet for Excel export.",
            len(scraped_data),
        )
        return scraped_data
