"""
Configuration and static test data module for OrangeHRM Automation.
Uses 100% built-in Python libraries to maintain fast build speeds and
zero external dependencies.
"""

import os
from pathlib import Path

import yaml

from src.security import decrypt_password_with_hashlib

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


# ENVIRONMENT & CONFIGURATION LOADING
# 1. Load local .env file manually (Zero external dependencies approach)

env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignore empty lines and comments, extract key-value pairs
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# 2. Load non-secret runtime configuration and external data locations.
config_path = PROJECT_ROOT / "config.yaml"
with config_path.open("r", encoding="utf-8") as config_file:
    config_data = yaml.safe_load(config_file) or {}

# Point the Robot Framework file and development data to their correct locations
ROBOT_FILE = BASE_DIR / "tasks.robot"
DEVDATA_DIR = BASE_DIR / "devdata"

# Keep generated files alongside the project configuration
OUTPUT_DIR = Path(
    os.getenv("ROBOT_OUTPUT_DIR", config_data.get("output_dir", "output"))
)
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = PROJECT_ROOT / OUTPUT_DIR

# Portal Credentials & URLs
BASE_URL = os.getenv("ORANGEHRM_BASE_URL", config_data["base_url"])
USERNAME = os.getenv("ORANGEHRM_USER", config_data.get("username", "Admin"))


# SECURE PASSWORD HANDLING ( hashlib + secret key)
SECRET_KEY = os.getenv("SECRET_KEY")

# Priority: config.json (encrypted) -> System Environment Variable -> Plaintext fallback
encrypted_password = os.getenv("ORANGEHRM_PASSWORD_ENCRYPTED")
if not encrypted_password:
    legacy_config_path = PROJECT_ROOT / "config.json"
    if legacy_config_path.exists():
        import json

        with legacy_config_path.open("r", encoding="utf-8") as config_file:
            encrypted_password = json.load(config_file).get(
                "ORANGEHRM_PASSWORD_ENCRYPTED"
            )

if os.getenv("ORANGEHRM_PASSWORD"):
    ORANGEHRM_PASSWORD = os.environ["ORANGEHRM_PASSWORD"]
elif encrypted_password:
    # Decrypt password securely at runtime for Selenium login
    if not SECRET_KEY:
        ORANGEHRM_PASSWORD = None
    else:
        ORANGEHRM_PASSWORD = decrypt_password_with_hashlib(
            encrypted_password, SECRET_KEY
        )
else:
    # Fallback in case the password is provided directly via an environment variable
    ORANGEHRM_PASSWORD = os.getenv("ORANGEHRM_PASSWORD")

# Backward compatibility alias for any modules importing 'PASSWORD'
PASSWORD = ORANGEHRM_PASSWORD

# Excel Output Paths
PRIMARY_EXCEL_PATH = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
ATTACHMENTS_EXCEL_PATH = OUTPUT_DIR / "OrangeHRM_Attachments.xlsx"
SAMPLE_ATTACHMENT_PATH = DEVDATA_DIR / "sample_attachment.pdf"


def validate_environment() -> None:
    """Create required directories and validate configured project fixtures."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SAMPLE_ATTACHMENT_PATH.exists():
        raise FileNotFoundError(
            f"Required attachment fixture not found: {SAMPLE_ATTACHMENT_PATH}"
        )


def validate_credentials() -> None:
    """Fail fast before a browser workflow starts without runtime secrets."""
    if not USERNAME or not PASSWORD:
        raise ValueError(
            "ORANGEHRM_USER and ORANGEHRM_PASSWORD must be provided through "
            "the environment or local .env file."
        )
    if encrypted_password and not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY is required when ORANGEHRM_PASSWORD_ENCRYPTED is used."
        )


MY_INFO_SECTIONS = (
    "Personal_Details",
    "Contact_Details",
    "Emergency_Contacts",
    "Dependents",
    "Immigration",
    "Job",
    "Salary",
    "Report_To",
    "Qualifications",
    "Memberships",
)


def format_my_info_section_label(section_name: str, position: int) -> str:
    """Return the numbered display label for a My Info section."""
    display_name = section_name.replace("_", " ").replace("Report To", "Report-to")
    return f"{position}. {display_name}"


# Phase 2: Timesheet Dummy Data
def _load_data_file(file_name: str) -> dict:
    data_path = DEVDATA_DIR / file_name
    with data_path.open("r", encoding="utf-8") as data_file:
        if data_path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(data_file)
        import json

        return json.load(data_file)


TIMESHEET_DATA = _load_data_file(config_data["data"]["timesheet"])

# Phase 3: 10 Sections of "My Info" Dummy Data
MY_INFO_SECTIONS_DATA = _load_data_file(config_data["data"]["my_info"])

HEADLESS = os.getenv("HEADLESS", str(config_data.get("headless", False))).lower() == "true"
BROWSER = os.getenv("BROWSER", config_data.get("browser", "chrome")).lower()
WAIT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT", config_data.get("wait_timeout", 20)))
RUN_EMAIL = os.getenv("RUN_EMAIL", str(config_data.get("run_email", True))).lower() == "true"
ROBOT_RETRIES = int(os.getenv("ROBOT_RETRIES", config_data.get("robot_retries", 1)))

# ==============================================================================
# PHASE 4: THUNDERBIRD EMAIL AUTOMATION CONFIGURATION
# ==============================================================================
TEAM_LEAD_EMAIL = os.getenv(
    "TEAM_LEAD_EMAIL", "fa22-bcs-260@students.cuisahiwal.edu.pk"
)
AUTOMATION_AUTHOR = os.getenv("AUTOMATION_AUTHOR", "Automation Bot")
EMAIL_1_SUBJECT = "OrangeHRM RPA Report: Weekly Timesheet Automation Summary"

# Standard Windows installation paths for Mozilla Thunderbird
THUNDERBIRD_PATHS = [
    Path(r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"),
    Path(r"C:\Program Files (x86)\Mozilla Thunderbird\thunderbird.exe"),
]
