"""Selenium locators used by the OrangeHRM page objects."""

from selenium.webdriver.common.by import By

Locator = tuple[str, str]


class BaseLocators:
    """Selectors shared by OrangeHRM page objects."""

    LOADING_SPINNER: Locator = (By.CSS_SELECTOR, "div.oxd-loading-spinner")
    FORM_LOADER: Locator = (By.CSS_SELECTOR, "div.oxd-form-loader")
    CALENDAR_WRAPPER: Locator = (By.CSS_SELECTOR, "div.oxd-calendar-wrapper")
    SUCCESS_TOAST: Locator = (
        By.XPATH,
        "//div[contains(@class, 'oxd-toast')]//*[contains(text(), 'Success') or contains(text(), 'Successfully') or contains(text(), 'Saved')]",
    )
    INPUT_ERROR: Locator = (
        By.CSS_SELECTOR,
        "span.oxd-input-field-error-message",
    )
    ATTACHMENT_ROWS: Locator = (
        By.XPATH,
        "//div[contains(@class, 'orangehrm-container')]//div[@class='oxd-table-body']//div[@role='row']",
    )
    ATTACHMENT_CELLS: Locator = (By.XPATH, ".//div[@role='cell']")
    SIDEBAR_ITEM_TEMPLATE = "//aside[@class='oxd-sidepanel']//span[normalize-space()={menu_name}]/ancestor::a"
    ATTACHMENT_ADD_BUTTON: Locator = (
        By.XPATH,
        (
            "//h6[normalize-space()='Attachments']"
            "/ancestor::div[contains(@class, 'orangehrm-action-header') or contains(@class, 'orangehrm-card-container')]"
            "//button[contains(., 'Add') or contains(@class, 'oxd-button')]"
        ),
    )
    ATTACHMENT_FILE_INPUT: Locator = (By.XPATH, "//input[@type='file']")
    ATTACHMENT_COMMENT: Locator = (
        By.XPATH,
        (
            "//h6[normalize-space()='Attachments']"
            "/ancestor::div[contains(@class, 'orangehrm-card-container') or contains(@class, 'orangehrm-horizontal-padding')]//textarea"
        ),
    )
    ATTACHMENT_SAVE_BUTTON: Locator = (
        By.XPATH,
        (
            "//h6[normalize-space()='Attachments']"
            "/ancestor::div[contains(@class, 'orangehrm-card-container') or contains(@class, 'orangehrm-horizontal-padding')]"
            "//button[@type='submit' and (normalize-space()='Save' or contains(., 'Save'))]"
        ),
    )
    DROPDOWN_OPTIONS: Locator = (
        By.XPATH,
        "//div[@role='listbox']//div[@role='option']//span",
    )

    @classmethod
    def sidebar_item(cls, menu_name: str) -> Locator:
        """Return the sidebar locator for a menu name.

        Args:
            menu_name (str): Visible sidebar menu name.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = BaseLocators.sidebar_item("Time")
        """
        return By.XPATH, cls.SIDEBAR_ITEM_TEMPLATE.format(
            menu_name=MyInfoLocators.xpath_literal(menu_name)
        )

    @classmethod
    def input_by_label(cls, label_text: str) -> Locator:
        """Return an input or textarea locator for a visible label.

        Args:
            label_text (str): Visible field label.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = BaseLocators.input_by_label("Employee Id")
        """
        value = MyInfoLocators.xpath_literal(label_text)
        return By.XPATH, (
            f"//label[normalize-space()={value}]"
            "/ancestor::div[contains(@class, 'oxd-input-group')]//input | "
            f"//label[normalize-space()={value}]"
            "/ancestor::div[contains(@class, 'oxd-input-group')]//textarea"
        )

    @classmethod
    def dropdown_by_label(cls, label_text: str) -> Locator:
        """Return a custom dropdown locator for a visible label.

        Args:
            label_text (str): Visible dropdown label.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = BaseLocators.dropdown_by_label("Country")
        """
        value = MyInfoLocators.xpath_literal(label_text)
        return By.XPATH, (
            f"//label[normalize-space()={value}]"
            "/ancestor::div[contains(@class, 'oxd-input-group')]"
            "//div[contains(@class, 'oxd-select-text-input')]"
        )

    @classmethod
    def dropdown_option(cls, option_text: str) -> Locator:
        """Return a listbox option locator for visible option text.

        Args:
            option_text (str): Visible option text.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = BaseLocators.dropdown_option("Pakistan")
        """
        return By.XPATH, (
            f"//div[@role='listbox']//span[normalize-space()="
            f"{MyInfoLocators.xpath_literal(option_text)}]"
        )


class LoginLocators:
    """Selectors for the OrangeHRM login page."""

    USERNAME_FIELD: Locator = (By.NAME, "username")
    PASSWORD_FIELD: Locator = (By.NAME, "password")
    LOGIN_BUTTON: Locator = (By.XPATH, "//button[@type='submit']")
    DASHBOARD_HEADER: Locator = (By.XPATH, "//h6[normalize-space()='Dashboard']")


class TimeLocators:
    """Selectors for the OrangeHRM timesheet page."""

    TIMESHEETS_TOP_MENU: Locator = (
        By.XPATH,
        "//nav[@aria-label='Topbar Menu']//span[contains(normalize-space(), 'Timesheets')]",
    )
    MY_TIMESHEETS_OPTION: Locator = (
        By.XPATH,
        "//ul[@class='oxd-dropdown-menu']//a[normalize-space()='My Timesheets']",
    )
    EDIT_BUTTON: Locator = (By.XPATH, "//button[normalize-space()='Edit']")
    CREATE_TIMESHEET_BUTTON: Locator = (
        By.XPATH,
        "//button[normalize-space()='Create Timesheet']",
    )
    SAVE_TIMESHEET_BUTTON: Locator = (
        By.XPATH,
        "//button[@type='submit' and normalize-space()='Save']",
    )
    EDITABLE_DATA_ROWS: Locator = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody/tr[.//input[contains(@placeholder, 'Type for hints')]]",
    )
    ADD_ROW_PLUS_BUTTON: Locator = (
        By.XPATH,
        (
            "//table[contains(@class, 'orangehrm-timesheet-table')]//td[contains(normalize-space(), 'Add Row')]//button | "
            "//table[contains(@class, 'orangehrm-timesheet-table')]//button[.//i[contains(@class, 'bi-plus')]]"
        ),
    )
    DELETE_ROW_BUTTONS: Locator = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody//i[contains(@class, 'bi-trash')]/ancestor::button",
    )
    AUTOCOMPLETE_VALID_OPTIONS: Locator = (
        By.XPATH,
        "//div[@role='listbox']//div[@role='option' and not(contains(normalize-space(), 'Searching')) and not(contains(normalize-space(), 'No Records Found'))]",
    )
    ACTIVITY_VALID_OPTIONS: Locator = (
        By.XPATH,
        "//div[@role='listbox']//div[@role='option' and not(contains(normalize-space(), '-- Select --')) and not(contains(normalize-space(), 'No Records Found'))]",
    )
    SAVED_TABLE_HEADERS: Locator = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//thead//th",
    )
    SAVED_TABLE_ROWS: Locator = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody//tr[not(contains(@class, '--total'))]",
    )
    INPUT_ERROR: Locator = (
        By.XPATH,
        "//span[contains(@class, 'oxd-input-field-error-message')]",
    )
    TABLE_CELL: Locator = (By.XPATH, ".//td")

    @classmethod
    def data_row(cls, row_num: int) -> str:
        """Return the XPath for a timesheet data row.

        Args:
            row_num (int): One-based row number.

        Returns:
            str: XPath expression.

        Example:
            xpath = TimeLocators.data_row(1)
        """
        return (
            "(//table[contains(@class, 'orangehrm-timesheet-table')]"
            "//tbody/tr[.//input[contains(@placeholder, 'Type for hints')]])"
            f"[{row_num}]"
        )

    @classmethod
    def project_input(cls, row_num: int) -> Locator:
        """Return the project autocomplete locator for a row.

        Args:
            row_num (int): One-based row number.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = TimeLocators.project_input(1)
        """
        return (
            By.XPATH,
            f"{cls.data_row(row_num)}//input[contains(@placeholder, 'Type for hints')]",
        )

    @classmethod
    def activity_dropdown(cls, row_num: int) -> Locator:
        """Return the activity dropdown locator for a row.

        Args:
            row_num (int): One-based row number.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = TimeLocators.activity_dropdown(1)
        """
        return (
            By.XPATH,
            f"{cls.data_row(row_num)}//div[contains(@class, 'oxd-select-text-input')]",
        )

    @classmethod
    def row_inputs(cls, row_num: int) -> Locator:
        """Return all input locators for a timesheet row.

        Args:
            row_num (int): One-based row number.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = TimeLocators.row_inputs(1)
        """
        return By.XPATH, f"{cls.data_row(row_num)}//input"


class MyInfoLocators:
    """Selectors for the OrangeHRM My Info page."""

    TAB_LINK_TEMPLATE = "//div[@role='tablist']//a[normalize-space()={tab_name}]"
    PRIMARY_SAVE_BUTTON: Locator = (
        By.XPATH,
        "(//form[@class='oxd-form']//button[@type='submit' and normalize-space()='Save'])[1]",
    )
    FIRST_NAME_FIELD: Locator = (By.NAME, "firstName")
    MIDDLE_NAME_FIELD: Locator = (By.NAME, "middleName")
    LAST_NAME_FIELD: Locator = (By.NAME, "lastName")
    ATTACHMENT_CELL: Locator = (By.XPATH, ".//div[@role='cell']")
    ATTACHMENT_ADD_BUTTON_TEMPLATE = (
        "//h6[normalize-space()='Attachments']"
        "/ancestor::div[contains(@class, 'orangehrm-action-header')]//button"
    )
    FILE_INPUT: Locator = (By.XPATH, "//input[@type='file']")

    @classmethod
    def tab_link(cls, tab_name: str) -> Locator:
        """Return the locator for a My Info tab.

        Args:
            tab_name (str): Visible tab name.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = MyInfoLocators.tab_link("Job")
        """
        return By.XPATH, cls.TAB_LINK_TEMPLATE.format(
            tab_name=cls.xpath_literal(tab_name)
        )

    @classmethod
    def section_add_button(cls, section_title: str) -> Locator:
        """Return the add-record button for a section heading.

        Args:
            section_title (str): Visible section heading.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = MyInfoLocators.section_add_button("Work Experience")
        """
        return By.XPATH, (
            f"//h6[normalize-space()={cls.xpath_literal(section_title)}]"
            "/ancestor::div[contains(@class, 'orangehrm-action-header')]//button"
        )

    @classmethod
    def attachment_add_button(cls) -> Locator:
        """Return the attachment add button locator.

        Args:
            None.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = MyInfoLocators.attachment_add_button()
        """
        return By.XPATH, cls.ATTACHMENT_ADD_BUTTON_TEMPLATE

    @classmethod
    def generic_section_rows(cls, header_title: str) -> Locator:
        """Return the table-row locator below a section heading.

        Args:
            header_title (str): Visible section heading.

        Returns:
            Locator: Selenium locator tuple.

        Example:
            locator = MyInfoLocators.generic_section_rows("Job History")
        """
        return By.XPATH, (
            f"//h6[normalize-space()={cls.xpath_literal(header_title)}]"
            "/ancestor::div[contains(@class, 'orangehrm-action-header') "
            "or contains(@class, 'orangehrm-horizontal-padding')]"
            "/following-sibling::div[contains(@class, 'orangehrm-container')][1]"
            "//div[@class='oxd-table-body']//div[@role='row']"
        )

    @staticmethod
    def xpath_literal(value: str) -> str:
        """Build an XPath string literal that supports apostrophes.

        Args:
            value (str): Text to encode.

        Returns:
            str: XPath string literal.

        Example:
            literal = MyInfoLocators.xpath_literal("Driver's License")
        """
        if "'" not in value:
            return f"'{value}'"
        parts = value.split("'")
        return "concat(" + ', "\'", '.join(f"'{part}'" for part in parts) + ")"
