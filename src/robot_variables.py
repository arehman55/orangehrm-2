import os

HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER = os.getenv("BROWSER", "chrome").lower()
RUN_EMAIL = os.getenv("RUN_EMAIL", "true").lower() == "true"
