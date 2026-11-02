"""
Phase 3: 'My Info' Module Automation & Scraping Page Object Model.
Automates data entry, PDF attachment uploads, save validations, and scraping across all 10 sections.
"""

import logging
from pathlib import Path
from typing import Any

from src.base_page import BasePage
from src.pages.locators import MyInfoLocators

logger = logging.getLogger(__name__)


class MyInfoPage(BasePage):
    """Page Object for the 10 sub-sections inside the OrangeHRM 'My Info' module."""

    PRIMARY_SAVE_BTN = MyInfoLocators.PRIMARY_SAVE_BUTTON

    def navigate_to_my_info(self) -> None:
        """Open the My Info module from the main sidebar.

        Args:
            None.

        Returns:
            None.

        Example:
            page.navigate_to_my_info()
        """

        logger.info("Navigating to My Info module...")
        self.navigate_sidebar("My Info")
        self.wait_for_loaders()

    def open_sub_tab(self, tab_name: str) -> None:
        """Click a tab inside the My Info module.

        Args:
            tab_name (str): Visible name of the tab to open.

        Returns:
            None.

        Example:
            page.open_sub_tab("Personal Details")
        """
        logger.info("Switching to My Info section: [%s]", tab_name)
        if getattr(self, "driver", None) is not None:
            self.driver.execute_script("window.scrollTo(0, 0);")
        self.click_element(MyInfoLocators.tab_link(tab_name))
        self.wait_for_loaders()

    def process_all_ten_sections(
        self,
        sections_data: dict[str, dict[str, Any]],
        attachment_file: Path,
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
        """
        Process, validate, and scrape all ten My Info sections.

        Args:
            sections_data (Dict[str, Dict[str, Any]]): Input data keyed by section name.
            attachment_file (Path): PDF file to upload in each applicable section.

        Returns:
            Tuple containing section data rows and attachment rows keyed by section.

        Example:
            sections, attachments = page.process_all_ten_sections(data, attachment)
        """
        self.navigate_to_my_info()

        all_sections_scraped: dict[str, list[dict[str, Any]]] = {}
        all_attachments_by_section: dict[str, list[dict[str, Any]]] = {}

        # 1. Personal Details
        sec_1, att_1 = self._handle_personal_details(
            sections_data["Personal_Details"], attachment_file
        )
        all_sections_scraped["Personal_Details"] = sec_1
        all_attachments_by_section["1. Personal Details"] = att_1

        # 2. Contact Details
        sec_2, att_2 = self._handle_contact_details(
            sections_data["Contact_Details"], attachment_file
        )
        all_sections_scraped["Contact_Details"] = sec_2
        all_attachments_by_section["2. Contact Details"] = att_2

        # 3. Emergency Contacts
        sec_3, att_3 = self._handle_emergency_contacts(
            sections_data["Emergency_Contacts"], attachment_file
        )
        all_sections_scraped["Emergency_Contacts"] = sec_3
        all_attachments_by_section["3. Emergency Contacts"] = att_3

        # 4. Dependents
        sec_4, att_4 = self._handle_dependents(
            sections_data["Dependents"], attachment_file
        )
        all_sections_scraped["Dependents"] = sec_4
        all_attachments_by_section["4. Dependents"] = att_4

        # 5. Immigration
        sec_5, att_5 = self._handle_immigration(
            sections_data["Immigration"], attachment_file
        )
        all_sections_scraped["Immigration"] = sec_5
        all_attachments_by_section["5. Immigration"] = att_5

        # 6. Job
        sec_6, att_6 = self._handle_job_section(attachment_file)
        all_sections_scraped["Job"] = sec_6
        all_attachments_by_section["6. Job"] = att_6

        # 7. Salary
        sec_7, att_7 = self._handle_salary_section(attachment_file)
        all_sections_scraped["Salary"] = sec_7
        all_attachments_by_section["7. Salary"] = att_7

        # 8. Report-to
        sec_8, att_8 = self._handle_report_to_section(attachment_file)
        all_sections_scraped["Report_To"] = sec_8
        all_attachments_by_section["8. Report-to"] = att_8

        # 9. Qualifications
        sec_9, att_9 = self._handle_qualifications(
            sections_data["Qualifications"], attachment_file
        )
        all_sections_scraped["Qualifications"] = sec_9
        all_attachments_by_section["9. Qualifications"] = att_9

        # 10. Memberships
        sec_10, att_10 = self._handle_memberships(
            sections_data["Memberships"], attachment_file
        )
        all_sections_scraped["Memberships"] = sec_10
        all_attachments_by_section["10. Memberships"] = att_10

        return all_sections_scraped, all_attachments_by_section

    # -------------------------------------------------------------------------
    # Individual Section Handlers (1 to 10)
    # -------------------------------------------------------------------------

    def _handle_personal_details(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Personal Details section.

        Args:
            data (Dict[str, Any]): Personal details to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped personal-detail rows and attachment rows.

        Example:
            rows, attachments = page._handle_personal_details(data, pdf_path)
        """
        self.open_sub_tab("Personal Details")

        self.clear_and_type(MyInfoLocators.FIRST_NAME_FIELD, data["first_name"])
        self.clear_and_type(MyInfoLocators.MIDDLE_NAME_FIELD, data["middle_name"])
        self.clear_and_type(MyInfoLocators.LAST_NAME_FIELD, data["last_name"])
        self.fill_field_by_label("Employee Id", data["employee_id"])
        self.fill_field_by_label("Other Id", data["other_id"])
        self.fill_field_by_label("Driver's License Number", data["drivers_license"])
        self.fill_field_by_label("License Expiry Date", data["license_expiry"])
        self.select_dropdown_by_label("Nationality", data["nationality"])
        self.select_dropdown_by_label("Marital Status", data["marital_status"])
        self.fill_field_by_label("Date of Birth", data["dob"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Personal Details - Official ID Document"
        )

        scraped = [
            {
                "First Name": self.find_visible(
                    MyInfoLocators.FIRST_NAME_FIELD
                ).get_attribute("value"),
                "Middle Name": self.find_visible(
                    MyInfoLocators.MIDDLE_NAME_FIELD
                ).get_attribute("value"),
                "Last Name": self.find_visible(
                    MyInfoLocators.LAST_NAME_FIELD
                ).get_attribute("value"),
                "Employee Id": self.read_field_by_label("Employee Id"),
                "Other Id": self.read_field_by_label("Other Id"),
                "Driver's License Number": self.read_field_by_label(
                    "Driver's License Number"
                ),
                "License Expiry Date": self.read_field_by_label("License Expiry Date"),
                "Nationality": self.read_dropdown_by_label("Nationality"),
                "Marital Status": self.read_dropdown_by_label("Marital Status"),
                "Date of Birth": self.read_field_by_label("Date of Birth"),
            }
        ]
        attachments = [
            self.capture_attachment_metadata_from_current_section("Personal Details")
        ]
        return scraped, attachments

    def _handle_contact_details(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Contact Details section.

        Args:
            data (Dict[str, Any]): Contact details to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped contact-detail rows and attachment rows.

        Example:
            rows, attachments = page._handle_contact_details(data, pdf_path)
        """
        self.open_sub_tab("Contact Details")

        self.fill_field_by_label("Street 1", data["street_1"])
        self.fill_field_by_label("Street 2", data["street_2"])
        self.fill_field_by_label("City", data["city"])
        self.fill_field_by_label("State/Province", data["state"])
        self.fill_field_by_label("Zip/Postal Code", data["zip_code"])
        self.select_dropdown_by_label("Country", data["country"])
        self.fill_field_by_label("Mobile", data["mobile"])
        self.fill_field_by_label("Work Email", data["work_email"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Contact Details - Residence Verification PDF"
        )

        scraped = [
            {
                "Street 1": self.read_field_by_label("Street 1"),
                "Street 2": self.read_field_by_label("Street 2"),
                "City": self.read_field_by_label("City"),
                "State/Province": self.read_field_by_label("State/Province"),
                "Zip/Postal Code": self.read_field_by_label("Zip/Postal Code"),
                "Country": self.read_dropdown_by_label("Country"),
                "Mobile": self.read_field_by_label("Mobile"),
                "Work Email": self.read_field_by_label("Work Email"),
            }
        ]
        attachments = [
            self.capture_attachment_metadata_from_current_section("Contact Details")
        ]
        return scraped, attachments

    def _handle_emergency_contacts(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Emergency Contacts section.

        Args:
            data (Dict[str, Any]): Emergency contact values to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped emergency-contact rows and attachment rows.

        Example:
            rows, attachments = page._handle_emergency_contacts(data, pdf_path)
        """
        self.open_sub_tab("Emergency Contacts")

        self.click_element(
            MyInfoLocators.section_add_button("Assigned Emergency Contacts")
        )

        self.fill_field_by_label("Name", data["name"])
        self.fill_field_by_label("Relationship", data["relationship"])
        self.fill_field_by_label("Home Telephone", data["home_telephone"])
        self.fill_field_by_label("Mobile", data["mobile"])
        self.fill_field_by_label("Work Telephone", data["work_telephone"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Emergency Contacts - Consent PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Emergency Contacts",
            ["Name", "Relationship", "Home Telephone", "Mobile", "Work Telephone"],
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Emergency Contacts")
        ]
        return scraped, attachments

    def _handle_dependents(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Dependents section.

        Args:
            data (Dict[str, Any]): Dependent values to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped dependent rows and attachment rows.

        Example:
            rows, attachments = page._handle_dependents(data, pdf_path)
        """
        self.open_sub_tab("Dependents")

        self.click_element(MyInfoLocators.section_add_button("Assigned Dependents"))

        self.fill_field_by_label("Name", data["name"])
        self.select_dropdown_by_label("Relationship", data["relationship"])
        self.fill_field_by_label("Date of Birth", data["dob"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Dependents - Birth Certificate PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Dependents", ["Name", "Relationship", "Date of Birth"]
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Dependents")
        ]
        return scraped, attachments

    def _handle_immigration(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Immigration section.

        Args:
            data (Dict[str, Any]): Immigration values to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped immigration rows and attachment rows.

        Example:
            rows, attachments = page._handle_immigration(data, pdf_path)
        """
        self.open_sub_tab("Immigration")

        self.click_element(
            MyInfoLocators.section_add_button("Assigned Immigration Records")
        )

        self.fill_field_by_label("Number", data["number"])
        self.fill_field_by_label("Issued Date", data["issued_date"])
        self.fill_field_by_label("Expiry Date", data["expiry_date"])
        self.fill_field_by_label("Eligible Status", data["eligible_status"])
        self.select_dropdown_by_label("Issued By", data["issued_by"])
        self.fill_field_by_label("Eligible Review Date", data["eligible_review_date"])
        self.fill_field_by_label("Comments", data["comments"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Immigration - Scanned Passport PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Immigration Records",
            ["Document", "Number", "Issued By", "Issued Date", "Expiry Date"],
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Immigration")
        ]
        return scraped, attachments

    def _handle_job_section(
        self, attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Scrape job details and upload an attachment when supported.

        Args:
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped job rows and attachment rows.

        Example:
            rows, attachments = page._handle_job_section(pdf_path)
        """
        self.open_sub_tab("Job")

        # Upload attachment if the Attachments header is present on the Job tab
        self._try_upload_attachment(attachment_file, "Job - Employment Contract PDF")

        scraped = [
            {
                "Joined Date": self.read_field_by_label("Joined Date"),
                "Job Title": self.read_dropdown_by_label("Job Title"),
                "Job Category": self.read_dropdown_by_label("Job Category"),
                "Sub Unit": self.read_dropdown_by_label("Sub Unit"),
                "Location": self.read_dropdown_by_label("Location"),
                "Employment Status": self.read_dropdown_by_label("Employment Status"),
            }
        ]
        attachments = [self.capture_attachment_metadata_from_current_section("Job")]
        return scraped, attachments

    def _handle_salary_section(
        self, attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Scrape salary components and upload an attachment.

        Args:
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped salary rows and attachment rows.

        Example:
            rows, attachments = page._handle_salary_section(pdf_path)
        """
        self.open_sub_tab("Salary")

        self._try_upload_attachment(
            attachment_file, "Salary - Approved Compensation PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Salary Components",
            [
                "Salary Component",
                "Amount",
                "Currency",
                "Pay Frequency",
                "Direct Deposit Amount",
            ],
        )
        attachments = [self.capture_attachment_metadata_from_current_section("Salary")]
        return scraped, attachments

    def _handle_report_to_section(
        self, attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Scrape reporting supervisors and upload an attachment.

        Args:
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped supervisor rows and attachment rows.

        Example:
            rows, attachments = page._handle_report_to_section(pdf_path)
        """
        self.open_sub_tab("Report-to")

        self._try_upload_attachment(
            attachment_file, "Report-to - Reporting Line Approval PDF"
        )

        supervisors = self._scrape_generic_section_table(
            "Assigned Supervisors", ["Name", "Reporting Method"]
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Report-to")
        ]
        return supervisors, attachments

    def _handle_qualifications(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Qualifications section.

        Args:
            data (Dict[str, Any]): Work experience values to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped qualification rows and attachment rows.

        Example:
            rows, attachments = page._handle_qualifications(data, pdf_path)
        """
        self.open_sub_tab("Qualifications")

        self.click_element(MyInfoLocators.section_add_button("Work Experience"))

        self.fill_field_by_label("Company", data["company"])
        self.fill_field_by_label("Job Title", data["job_title"])
        self.fill_field_by_label("From", data["from_date"])
        self.fill_field_by_label("To", data["to_date"])
        self.fill_field_by_label("Comment", data["comment"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Qualifications - Experience Certificate PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Work Experience",
            ["Company", "Job Title", "From", "To", "Comment"],
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Qualifications")
        ]
        return scraped, attachments

    def _handle_memberships(
        self, data: dict[str, Any], attachment_file: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and scrape the Memberships section.

        Args:
            data (Dict[str, Any]): Membership values to enter.
            attachment_file (Path): File to upload for the section.

        Returns:
            Tuple of scraped membership rows and attachment rows.

        Example:
            rows, attachments = page._handle_memberships(data, pdf_path)
        """
        self.open_sub_tab("Memberships")

        self.click_element(MyInfoLocators.section_add_button("Assigned Memberships"))

        self.select_dropdown_by_label("Membership", index=2)
        self.select_dropdown_by_label(
            "Subscription Paid By", data["subscription_paid_by"]
        )
        self.fill_field_by_label("Subscription Amount", data["subscription_amount"])
        self.select_dropdown_by_label("Currency", index=2)
        self.fill_field_by_label("Subscription Commence Date", data["commence_date"])
        self.fill_field_by_label("Subscription Renewal Date", data["renewal_date"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.wait_for_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Memberships - Subscription Receipt PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Memberships",
            [
                "Membership",
                "Subscription Paid By",
                "Subscription Amount",
                "Currency",
                "Subscription Commence Date",
                "Subscription Renewal Date",
            ],
        )
        attachments = [
            self.capture_attachment_metadata_from_current_section("Memberships")
        ]
        return scraped, attachments

    def _scrape_generic_section_table(
        self, header_title: str, columns: list[str]
    ) -> list[dict[str, Any]]:
        """
        Scrape an OrangeHRM table positioned below a section header.

        Args:
            header_title (str): Visible heading above the table.
            columns (List[str]): Output names for table columns.

        Returns:
            List of dictionaries containing scraped table records.

        Example:
            rows = page._scrape_generic_section_table("Work Experience", columns)
        """
        self.wait_for_loaders()
        rows = self.driver.find_elements(
            *MyInfoLocators.generic_section_rows(header_title)
        )
        results: list[dict[str, Any]] = []

        for row in rows:
            cells = row.find_elements(*MyInfoLocators.ATTACHMENT_CELL)
            if len(cells) > 1:
                record: dict[str, Any] = {}
                for i, col_name in enumerate(columns):
                    cell_idx = i + 1
                    record[col_name] = (
                        cells[cell_idx].text.strip() if cell_idx < len(cells) else ""
                    )
                results.append(record)

        if not results:
            results.append({col: "No Records Found" for col in columns})
        return results
