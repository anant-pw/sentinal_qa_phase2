import pytest
import os
import shutil
import subprocess
import allure
from loguru import logger
import os
from dotenv import load_dotenv
from loguru import logger
import requests

load_dotenv()

# The single point of truth for the entire framework
API_URL = os.getenv("SENTINEL_API_URL", "http://localhost:8000/plans")

APPROVED_DIR = "data/test_plans/approved"
ALLURE_RESULTS = "allure-results"
ALLURE_REPORT  = "allure-report"

# ── History preservation ───────────────────────────────────────────────────
# Allure tracks trends (pass/fail over time) via a `history` subfolder.
# Without this, every run starts fresh with no historical context.
# This hook runs once at session start — it copies the history from the
# last generated report back into allure-results so Allure can append to it.
def pytest_configure(config):
    logger.add("sentinel_run.log", rotation="10 MB")
    history_src  = os.path.join(ALLURE_REPORT, "history")
    history_dest = os.path.join(ALLURE_RESULTS, "history")

    if os.path.exists(history_src):
        if os.path.exists(history_dest):
            shutil.rmtree(history_dest)
        shutil.copytree(history_src, history_dest)
        logger.info("📊 Allure history restored from previous report.")
    else:
        logger.info("📊 No previous Allure history found — this will be run #1.")

# ── Auto-generate + open report after session ends ─────────────────────────
# Generates a persistent allure-report/ folder after every run and opens it
# in the browser automatically — no need to run allure serve manually.
def pytest_sessionfinish(session, exitstatus):
    logger.info("📊 Generating Allure report...")
    try:
        subprocess.run(
            ["allure", "generate", ALLURE_RESULTS, "--clean", "-o", ALLURE_REPORT],
            check=True
        )
        logger.success(f"✅ Allure report generated at: {ALLURE_REPORT}/")
        subprocess.Popen(["allure", "open", ALLURE_REPORT])
        logger.success("🌐 Allure report opened in browser.")
    except FileNotFoundError:
        logger.warning("⚠️  Allure CLI not found — run 'allure serve allure-results' manually.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Allure generation failed: {e}")

# ── Test parametrization ───────────────────────────────────────────────────
def pytest_generate_tests(metafunc):
    """Fetch Approved test cases from FastAPI instead of direct DB access."""
    if "test_case" in metafunc.fixturenames:
        try:
            # Fetch only 'approved' plans from the service
            response = requests.get(f"{API_URL}?status=approved", timeout=5)
            response.raise_for_status()
            plans = response.json()
        except Exception as e:
            logger.error(f"❌ Failed to fetch test plans from API: {e}")
            plans = []

        test_data = []
        ids = []

        for plan in plans:
            # Sort steps by sequence to ensure execution order
            steps = sorted(plan['steps'], key=lambda s: s['sequence'])
            
            # Format to match what test_engine.py expects
            test_dict = {
                "id": plan['id'], 
                "title": plan['title'],
                "steps": [
                    {"action": s['action'], "selector": s['selector'], "data": s['data']} 
                    for s in steps
                ]
            }
            test_data.append(test_dict)
            ids.append(plan['title'])

        metafunc.parametrize("test_case", test_data, ids=ids)

# ── Screenshot on failure ──────────────────────────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture full-page screenshot on failure and attach to Allure."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(
                page.screenshot(full_page=True),
                name="failure_screenshot",
                attachment_type=allure.attachment_type.PNG
            )
            logger.error(f"Test Failed: {item.nodeid} - Screenshot captured.")
