"""
Custom Exception Classes for OrangeHRM Enterprise RPA & Web Scraping Suite.
Defines domain-specific exceptions for robust error handling across all phases.
"""


class OrangeHRMBaseException(Exception):
    """Base exception for all OrangeHRM automation errors."""


class AuthenticationError(OrangeHRMBaseException):
    """Raised when Phase 1 login or dashboard validation fails."""


class TimesheetAutomationError(OrangeHRMBaseException):
    """Raised when Phase 2 timesheet entry, row addition, or saving fails."""


class MyInfoAutomationError(OrangeHRMBaseException):
    """Raised when Phase 3 data entry, tab switching, or form submission fails."""


class AttachmentUploadError(OrangeHRMBaseException):
    """Raised when file upload or scraping/downloading attachments fails."""


class ExcelExportError(OrangeHRMBaseException):
    """Raised when Pandas or Openpyxl fails to write, style, or format workbooks."""


class EmailAutomationError(OrangeHRMBaseException):
    """Raised when Phase 4 Thunderbird desktop email composition, attachment, or reply fails."""
