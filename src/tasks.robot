*** Settings ***
Documentation     Enterprise RPA & Web Scraping Suite for OrangeHRM Demo Portal.
...               Automates Login, 7-Day Timesheets, 10 My Info Sections, Excel Reporting,
...               and Thunderbird HTML Email Dispatch.
Library           src.keywords.orangehrm_keywords.OrangeHRMKeywords
Suite Teardown    Close Browser Safely
Variables         ${EXECDIR}/src/robot_variables.py

*** Tasks ***
Run OrangeHRM Enterprise Automation
    [Documentation]    Executes the complete 4-phase OrangeHRM RPA and Thunderbird Email workflow.
    Initialize Browser Session    headless=${HEADLESS}    browser=${BROWSER}

    Log To Console    \n[Phase 1] Authenticating with OrangeHRM Portal...
    Execute Phase 1 Authentication

    Log To Console    [Phase 2] Automating and Scraping 'Time -> My Timesheets' (7 Separate Daily Entries)...
    Execute Phase 2 Time Module Automation And Scraping

    Log To Console    [Phase 3] Automating and Scraping all 10 'My Info' Sections & Attachments...
    Execute Phase 3 My Info Automation And Scraping

    Log To Console    [Phase 4] Sending HTML Tabular Reports & Excel Attachments via Thunderbird...
    Run Keyword If    '${RUN_EMAIL}' == 'True'    Execute Phase 4 Email Reporting Via Thunderbird

    Log To Console    [Success] All 4 Phases completed and emails dispatched via Thunderbird!



#            /////// Testing Only: Thunderbird Email Automation ///////

# *** Settings ***
# Documentation     Temporary test for Thunderbird Email Automation.
# Library           src.keywords.orangehrm_keywords.OrangeHRMKeywords

# *** Tasks ***
# Test Thunderbird Email Only
#     [Documentation]    Directly executes Phase 4 email reporting using existing Excel files.
#     Log To Console    \n[Test Mode] Running Thunderbird Email Automation Only...
#     Execute Phase 4 Email Reporting Via Thunderbird
#     Log To Console    [Success] Email test completed!