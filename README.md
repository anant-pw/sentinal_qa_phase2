# 🛡️ Sentinel QA — Cognitive Autonomous Testing Ecosystem

> From Scripted Testing to Autonomous Testing Agents: How Playwright + LLMs Turn Manual Scripts into Self-Driving QA

Sentinel is a self-healing, AI-augmented quality ecosystem built entirely on open-source technology. It transforms unstructured requirements into executed, reported, and triaged test cases — with a human approval gate at every critical decision point.

---

## Architecture

```
Unstructured Requirement
        ↓
RequirementAnalyst (LangChain LCEL + SambaNova)
        ↓
POST /plans → FastAPI → SQLite DB
        ↓
Streamlit HITL Portal  ←→  Human Review & Approval
        ↓
conftest.py fetches approved plans via GET /plans
        ↓
pytest + Playwright Execution Engine
        ↓
    PASS ──────────────────────────────→ Allure Report
    FAIL → BugReporter (AI Triage)
              ↓              ↓
         DB Memory      Jira Ticket
         (history)    + Screenshot
              ↓
         Allure Report (AI Analysis attached)
```

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Automation | Playwright (sync mode) |
| Test Runner | Pytest + pytest-xdist |
| AI Orchestration | LangChain LCEL (ChatPromptTemplate \| model) |
| LLM Providers | SambaNova (Llama 3.3 70B) → Groq → Ollama |
| API Layer | FastAPI + Uvicorn + Pydantic |
| Database | SQLite (SQLAlchemy ORM — swap to PostgreSQL in one line) |
| Approval UI | Streamlit |
| Bug Tracking | Jira (atlassian-python-api) |
| Reporting | Allure (with AI Bug Analysis attached per failure) |

---

## Project Structure

```
sentinel_qa/
├── agents/
│   ├── requirement_analyst.py   # Converts requirements → JSON test plans via LLM
│   └── bug_reporter.py          # AI triage agent with DB-backed pattern memory
├── api/
│   ├── main.py                  # FastAPI routes (plans, results, approve, claim)
│   └── schemas.py               # Pydantic validation schemas
├── core/
│   ├── action_registry.py       # Playwright action library (navigate, type, click, verify)
│   ├── ai_factory.py            # LLM provider switcher (SambaNova → Groq → Ollama)
│   ├── api_client.py            # Pre-test API contract validation
│   ├── db_client.py             # SQLAlchemy session manager
│   ├── jira_client.py           # Jira bug creation + screenshot attachment
│   └── models.py                # SQLAlchemy ORM models (TestPlan, TestStep, TestResult)
├── tests/
│   └── test_engine.py           # Main execution engine (parametrized from DB)
├── ui/
│   └── approval_app.py          # Streamlit Human-in-the-Loop approval portal
├── scripts/
│   └── migrate_yamls.py         # One-time migration from YAML pilot to DB
├── conftest.py                  # pytest hooks: API fetch, Allure history, screenshots
├── config.yaml                  # Base URL, AI provider, model config
├── pytest.ini                   # pytest configuration
└── requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure `.env`

```env
# AI Providers
SAMBANOVA_API_KEY=your_key
GROQ_API_KEY=your_key
OLLAMA_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./sentinel.db

# Sentinel API
SENTINEL_API_URL=http://localhost:8000/plans

# Jira
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_token
JIRA_PROJECT_KEY=QA
JIRA_ISSUE_TYPE=Bug
```

### 3. Configure `config.yaml`

```yaml
project: "OrangeHRM-Pilot"
ai_provider: "sambanova"   # sambanova | groq | ollama
base_url: "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login"
model: "Meta-Llama-3.3-70B-Instruct"
```

---

## Running Sentinel

Sentinel requires three terminals running simultaneously:

**Terminal 1 — Start the API**
```bash
uvicorn api.main:app --reload
```

**Terminal 2 — Start the HITL Approval Portal**
```bash
streamlit run ui/approval_app.py
```

**Terminal 3 — Generate a test plan from a requirement**
```bash
python agents/requirement_analyst.py
```
Review and approve the generated plan at `http://localhost:8501`, then run the tests:

```bash
pytest
```

The Allure report opens automatically in your browser after the run completes.

---

## How Each Component Works

### 🧠 RequirementAnalyst
Reads unstructured requirement text, constructs a structured prompt via LangChain, and sends the AI-generated JSON test plan to `POST /plans`. The plan enters the DB with `status=pending`.

### 🛑 HITL Approval Portal (Streamlit)
Fetches all pending plans from `GET /plans?status=pending`. A human reviewer can edit individual steps inline via a data editor, then approve via `PATCH /plans/{id}/approve`. Edited steps are saved back to DB via `PUT /plans/{id}/steps` before approval.

### ⚙️ Execution Engine (pytest + Playwright)
`conftest.py` fetches all approved plans from the API at collection time and parametrizes the test suite dynamically. Each plan becomes one test case. `ActionRegistry` executes each step with wait strategies on every action to prevent SPA race conditions.

### 🔗 API Contract Validation (Two-Tier)
Before the browser opens, Sentinel runs:
- **Tier 1** — Hard fail if the target site returns non-200
- **Tier 2** — JSON contract assertion on the auth API (soft warn if non-JSON returned)

### 🤖 BugReporter (AI Triage Agent)
On failure, the LCEL chain queries DB for the last 5 failures on the same selector, injects that history as pattern context into the prompt, and generates a Jira-ready bug report identifying whether this is a recurring or isolated issue. The failure is then persisted to DB for future runs.

### 🎫 Jira Integration
`JiraClient` creates a bug ticket with the AI-generated report as the description, labels it `Sentinel-QA` and `AI-Generated`, and attaches the full-page failure screenshot.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/plans?status=pending\|approved` | Fetch plans by status |
| `POST` | `/plans` | Submit new AI-generated test plan |
| `PATCH` | `/plans/{id}/approve` | Approve a pending plan |
| `PUT` | `/plans/{id}/steps` | Save edited steps from Streamlit |
| `PATCH` | `/plans/{id}/claim` | xdist worker claims test (prevents collision) |
| `DELETE` | `/plans/{id}` | Delete a plan |
| `POST` | `/results` | Log a test result |
| `GET` | `/results/history/{selector}` | Fetch failure history for a selector |

Full interactive docs available at `http://localhost:8000/docs` when the API is running.

---

## AI Provider Fallback Chain

```
SambaNova (primary) → Groq (fallback) → Ollama (local fallback)
```

Switch providers by changing `ai_provider` in `config.yaml`. No code changes required.

---

## Phase Roadmap

| Phase | Status | Description |
|---|---|---|
| Pilot | ✅ Complete | Single-node, YAML-based, proof of concept |
| Phase 2 | ✅ Complete | FastAPI + SQLite + Jira + DB-backed AI memory |
| Phase 3 | 🔄 In Progress | xdist parallel execution, CI/CD, Allure Cloud |
| Phase 4 | 📋 Planned | Self-healing selectors written back to DB by AI |

---

## Key Design Decisions

**HITL gate is mandatory** — AI generates, humans approve, Playwright executes. This sequencing prevents AI hallucinations from reaching execution.

**DB-backed memory over session memory** — `BugReporter` queries historical failures across runs, not just the current session. By run 3, the AI can identify selectors that fail consistently across pipeline executions.

**FastAPI decouples all components** — `RequirementAnalyst`, Streamlit, and pytest all communicate through the API, not the filesystem. This is what makes xdist and CI/CD integration possible.

**Provider fallback chain** — Sentinel never hard-stops because one LLM provider is unavailable.

---

## Contributing

Built by [@yourusername](https://linkedin.com/in/yourprofile) as part of the **Sentinel Series** — documenting the evolution from manual QA scripting to fully autonomous AI-driven testing pipelines.
