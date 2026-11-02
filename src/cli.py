"""
Centralized Entry Point for the OrangeHRM & Thunderbird RPA Automation Package.
Allows initiating the complete end-to-end Robot Framework suite, Pure Python workflow,
or isolated Phase 4 Email Automation directly from the command line.
"""

import argparse
import logging
import sys

# Import the dynamically configured paths.
from src import config
from src.exceptions import OrangeHRMBaseException
from src.keywords.orangehrm_keywords import OrangeHRMKeywords
from src.robot_runner import run_robot_suite

logger = logging.getLogger("CentralizedRunner")


def run_robot_suite() -> int:
    """Run the complete automation suite through Robot Framework.

    Args:
        None.

    Returns:
        int: Robot Framework process return code.

    Example:
        exit_code = run_robot_suite()
    """
    logger.info(
        "Initiating Full RPA Suite via Robot Framework (%s)...", config.ROBOT_FILE.name
    )

    return_code = run_robot_suite(
        robot_file=config.ROBOT_FILE,
        output_dir=config.OUTPUT_DIR,
        browser=config.BROWSER,
        headless=config.HEADLESS,
        retries=config.ROBOT_RETRIES,
    )
    return int(return_code)


def run_pure_python_workflow(mode: str) -> None:
    """Run the automation phases through the Python keyword library.

    Args:
        mode (str): Execution mode, including ``email-only``.

    Returns:
        None.

    Example:
        run_pure_python_workflow("email-only")
    """
    rpa = OrangeHRMKeywords()

    if mode == "email-only":
        logger.info("Initiating Phase 4: Thunderbird Email Automation Only...")
        rpa.execute_phase_4_email_reporting()
        logger.info("Phase 4 Email Automation completed successfully!")
        return

    logger.info("Initiating Complete 4-Phase Pure Python Execution...")
    try:
        rpa.initialize_browser_session()
        rpa.execute_phase_1_authentication()
        rpa.execute_phase_2_time_module()
        rpa.execute_phase_3_my_info_module()
        rpa.execute_phase_4_email_reporting()
        logger.info("All 4 Phases completed successfully!")
    finally:
        rpa.close_browser_safely()


def main() -> None:
    """Parse command-line arguments and start the selected workflow.

    Args:
        None.

    Returns:
        None.

    Example:
        main()
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="OrangeHRM Enterprise RPA Centralized Runner"
    )
    parser.add_argument(
        "--mode",
        choices=["robot", "python", "email-only"],
        default="robot",
        help=(
            "'robot': Run full suite via tasks.robot (default) | "
            "'python': Run all 4 phases directly via Python | "
            "'email-only': Run only Phase 4 Thunderbird email automation"
        ),
    )
    args = parser.parse_args()

    try:
        config.validate_environment()
        if args.mode == "robot":
            config.validate_credentials()
            exit_code = run_robot_suite()
            sys.exit(exit_code)
        else:
            if args.mode == "python":
                config.validate_credentials()
            run_pure_python_workflow(args.mode)
    except (OSError, RuntimeError, ValueError, OrangeHRMBaseException) as exc:
        print(f"Execution failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
