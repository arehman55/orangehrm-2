# Enterprise RPA Automation Suite: OrangeHRM and Thunderbird

An end-to-end Robotic Process Automation (RPA) suite built with Python, Robot
Framework, Selenium, and RPA.Desktop. The application automates OrangeHRM
data collection, native Excel encryption, report generation, and desktop email
dispatch through Mozilla Thunderbird.

## Automation Workflow

The suite executes the following four phases:

1. **Secure authentication**
   Logs in to the OrangeHRM portal using Selenium.
2. **Timesheet data extraction**
   Navigates to the Time module, collects employee timesheet records, and
   prepares the data for reporting.
3. **Employee data and Excel generation**
   Extracts information from ten My Info sections and generates formatted Excel
   workbooks. The workbooks are protected with native Office AES encryption
   using `msoffcrypto`.
4. **Desktop email automation**
   Controls Mozilla Thunderbird using CLI compose commands, native window
   locators, and keyboard shortcuts. The timesheet report is sent as an HTML
   email, followed by a threaded reply containing the encrypted workbook and
   password instructions.

## Prerequisites

Install and configure the following before running the suite:

1. Python 3.9 or later.
2. Mozilla Thunderbird with the sender's email account configured.
3. Google Chrome for Selenium-based web automation.
4. Windows 10 or later, or a supported Ubuntu/Linux desktop environment.

The project also requires valid OrangeHRM credentials and the required secret
key configuration. See `config.json` and the environment variables used by
`src/config.py`.

## Installation

The project follows the PEP 621 packaging standard and can be installed from
source or from a built wheel.

### Install From Source

```bash
python -m venv rpa-env

# Linux and macOS
source rpa-env/bin/activate

# Windows PowerShell
# .\rpa-env\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install .
```

### Install From a Wheel

```bash
python -m pip install dist/orangehrm_rpa_automation-1.0.0-py3-none-any.whl
```

## Running the Automation

Installation registers the `run-rpa` command, which can be called from the
project directory or another working directory.

### Run the Complete Suite with Python

```bash
run-rpa --mode python
```

### Run with Robot Framework

```bash
run-rpa --mode robot
```

### Run Email Dispatch Only

```bash
run-rpa --mode email-only
```

## Architecture and Security

  `src/pages/locators.py` to keep browser interactions maintainable.
  files using a native Office encryption container. The resulting files can be
  opened in Microsoft Excel and compatible mobile viewers with the password.
  Windows uses native Win32 APIs. RPA.Desktop provides keyboard control for
  the final dispatch action.
  Snap, GTK, and Wayland environment variables removed where required.

## Testing

Run the unit tests without launching a browser or Thunderbird:

```bash
python -m pytest
```

## Building a Release

The build script removes stale build artifacts and creates a fresh wheel in the
`dist/` directory:

```bash
python build_script.py
```

## Generated Output

Successful execution creates an `output/` directory containing:

  workbook attached to the primary email.
  attached to the threaded reply.

# OrangeHRM RPA Automation

Enterprise-style Robot Framework automation for OrangeHRM, with Selenium page
objects, external test data, Excel reporting, Allure evidence, retry-aware CI,
and optional Thunderbird dispatch.

## Architecture

```text
src/tasks.robot                    Robot task orchestration
src/keywords/                      Robot-to-Python keyword boundary
src/pages/                         Selenium Page Object Model and locators
src/base_page.py                   Explicit waits and reusable browser actions
src/devdata/                       JSON data fixtures for data-driven flows
src/config.py                      YAML and environment configuration
src/robot_runner.py                Retry-aware Robot execution
src/reporting.py                   Allure failure screenshot listener
tests/                             Fast Python unit tests
.github/workflows/main.yml         CI matrix and artifact publishing
Dockerfile                         Reproducible headless browser image
docker-compose.yml                 Secret-injected local container execution
```

## Technology Stack

- Python 3.9+
- Robot Framework and RobotCode
- Selenium WebDriver with Chrome and Firefox
- Allure Robot Framework integration
- PyYAML, pandas, openpyxl, and msoffcrypto-tool
- GitHub Actions and Docker Compose

## Prerequisites

For local browser execution, install Python 3.9+, Chrome or Firefox, and a
valid OrangeHRM account. Thunderbird is required only when `RUN_EMAIL=true`.
Docker users need Docker Engine and the Compose plugin; the image installs
headless Chrome and Firefox automatically.

Create local configuration without committing credentials:

```bash
cp .env.example .env
# Edit .env and set ORANGEHRM_PASSWORD and SECRET_KEY.
```

`config.yaml` contains non-secret defaults. Environment variables override it.
Never commit `.env`, passwords, or encryption keys.

## Local Setup and Execution

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Run the fast unit suite:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Run the Robot workflow headlessly. Failed tasks are automatically rerun once
by default; configure `ROBOT_RETRIES` for a different retry budget.

```bash
HEADLESS=true RUN_EMAIL=false run-rpa --mode robot
```

Select a browser and timeout through environment variables:

```bash
BROWSER=firefox WAIT_TIMEOUT=30 ROBOT_RETRIES=2 run-rpa --mode robot
```

## Docker

The container is intended for browser automation. Thunderbird dispatch is
disabled because it requires a desktop session.

```bash
export ORANGEHRM_PASSWORD='your-password'
export SECRET_KEY='a-long-runtime-secret'
docker compose up --build --abort-on-container-exit
```

Choose Firefox with `BROWSER=firefox docker compose up --build` and inspect
the mounted `output/` directory after the run.

## Reports and Failure Evidence

Every run writes Robot output, log, report, retry XML, and screenshots under
`output/` (or `ROBOT_OUTPUT_DIR`). Allure result files are generated alongside
the run artifacts by the Allure Robot listener.

Install the Allure CLI separately, then generate and open the report:

```bash
allure generate output --clean -o output/allure-report
allure open output/allure-report
```

When a task fails while a browser is active, `AllureFailureListener` captures
the current Selenium screen and attaches it to the failed task. The raw PNG is
also retained in the output directory.

## Data-Driven Testing

Timesheet and My Info inputs live in `src/devdata/timesheet.json` and
`src/devdata/my_info.json`. Their paths are configured in `config.yaml`, so a
different fixture set can be selected without changing Robot tasks or page
objects.

## CI/CD

GitHub Actions runs the unit suite on Python 3.10, 3.11, and 3.12. When the
repository has the required secrets, the browser job runs the Robot workflow
headlessly on Chrome and Firefox and uploads each browser's output and Allure
evidence as an artifact.

Configure these repository secrets or variables:

- `ORANGEHRM_PASSWORD` secret
- `ORANGEHRM_USER` secret or variable, defaulting to `Admin`
- `SECRET_KEY` secret
- `ORANGEHRM_BASE_URL` repository variable, optional

## Project Commands

```bash
python -m src.cli --mode robot       # Robot task suite
python -m src.cli --mode python      # Direct Python phases
python -m src.cli --mode email-only  # Thunderbird dispatch only
python build_script.py               # Build a wheel
```