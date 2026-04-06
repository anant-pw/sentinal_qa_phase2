import os

import allure
import pytest
from core.action_registry import ActionRegistry
from core.api_client import APIClient
from agents.bug_reporter import BugReporter
from loguru import logger
logger.add("sentinel_run.log", rotation="10 MB")


def test_sentinel_executor(page, test_case):
    """
    Main execution engine that processes approved YAML test plans.
    shared_memory is injected from conftest (session scope) and passed
    into BugReporter so the AI can spot recurring failures across tests.
    """
    allure.dynamic.title(test_case.get('title', 'Untitled Test Case'))
    logger.info(f"🚀 Starting Test: {test_case.get('title')}")

    # ── Pre-test API contract validation ──────────────────────────────────
    # Two-tier check:
    #   Tier 1 — Reachability: the login page must return 200, not 4xx/5xx.
    #            If the site is down, we hard-fail immediately.
    #   Tier 2 — JSON contract: if the API endpoint returns JSON, we assert
    #            the shape. If it returns HTML (demo site behaviour), we skip
    #            the body check and log a warning — the UI test still runs.
    #
    # This design keeps the "genuine API assertion" honest without hard-coding
    # assumptions about the demo site's undocumented internal API structure.
    api = APIClient("https://opensource-demo.orangehrmlive.com/web/index.php")

    with allure.step("Tier 1 — Reachability check (GET login page)"):
        status, _ = api.check_health("auth/login")
        allure.attach(str(status), name="Login Page HTTP Status")
        assert status == 200, \
            f"Site unreachable — login page returned HTTP {status}. Aborting UI test."
        logger.info(f"✅ Tier 1 passed — login page reachable (HTTP {status})")

    with allure.step("Tier 2 — JSON contract check (POST auth/login API)"):
        api_status, body = api.post_login(username="Admin", password="admin123")
        allure.attach(str(api_status), name="API Login Status Code")
        allure.attach(str(body), name="API Login Response Body")

        if body:
            # JSON returned — assert the contract properly
            assert "status" in body, \
                f"API contract broken: 'status' key missing. Got: {body}"
            assert body.get("status") == "success", \
                f"API contract broken: expected status='success', got '{body.get('status')}'"
            assert body.get("user") is not None, \
                f"API contract broken: 'user' key is null. Got: {body}"
            logger.info("✅ Tier 2 passed — JSON contract verified (status=success, user present)")
        else:
            # Demo site returned HTML or empty — soft warning, don't block UI test
            logger.warning(
                f"⚠️ Tier 2 skipped — API returned non-JSON response (HTTP {api_status}). "
                "This is expected on the OrangeHRM public demo. UI test will proceed."
            )
            allure.attach(
                f"API returned non-JSON (HTTP {api_status}). Contract check skipped.",
                name="Tier 2 Warning",
                attachment_type=allure.attachment_type.TEXT
            )

    # ── Step-by-step UI execution ─────────────────────────────────────────
    steps = test_case.get('steps', [])
    try:
        for i, step in enumerate(steps):
            action_name = step.get('action')
            selector = step.get('selector')
            data = step.get('data')

            with allure.step(f"Step {i+1}: {action_name} | {selector if selector else ''}"):
                action_func = getattr(ActionRegistry, action_name)
                action_func(page, selector, data) if selector else action_func(page, data)

    except Exception as e:
            logger.error(f"❌ TEST FAILED: {e}")
            screenshot_path = os.path.abspath("failure_report.png")
            page.screenshot(path=screenshot_path)

            try:
                # Phase 2 BugReporter uses DB, no shared_memory needed
                reporter = BugReporter() 
                # Use the process_failure method we designed for Jira/DB sync
                jira_key = reporter.process_failure(
                    plan_id=test_case.get('id'),
                    test_case=test_case,
                    error_message=str(e),
                    screenshot_path=screenshot_path
                )
                
                if jira_key:
                    allure.attach(f"Jira Ticket Created: {jira_key}", name="Jira_Reference")
                    logger.success(f"🤖 AI Triage complete. Jira: {jira_key}")
                    
            except Exception as ai_err:
                logger.warning(f"AI Reporter failed: {ai_err}")

            raise e
