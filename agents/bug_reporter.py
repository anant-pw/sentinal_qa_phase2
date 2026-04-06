from core.ai_factory import AIFactory
from core.db_client import DBClient
from core.models import TestResult
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from core.jira_client import JiraClient


class BugReporter:
    def __init__(self):
        self.jira_client = JiraClient()
        self.llm = AIFactory.get_model()
        self.db = DBClient()
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a Senior QA Lead. Analyze failure patterns across history."),
            ("human", "HISTORY CONTEXT:\n{pattern_context}\n\nNEW FAILURE:\nTest: {title}\nError: {error_message}\nSteps:\n{steps_text}\n\nDraft a JIRA bug report identifying if this is a RECURRING or NEW issue.")
        ])
        self.chain = self.prompt_template | self.llm

    def _get_history(self, selector: str):
        session = self.db.get_session()
        history = session.query(TestResult).filter_by(failing_selector=selector).limit(5).all()
        session.close()
        if not history:
            return "This is the first time this selector has failed in recorded history."
        lines = [f"- Failed on {h.created_at} with error: {h.error_message[:50]}..." for h in history]
        return "\n".join(lines)

    def log_failure(self, plan_id: int, selector: str, error: str):
        session = self.db.get_session()
        result = TestResult(plan_id=plan_id, status="failed", failing_selector=selector, error_message=error)
        session.add(result)
        session.commit()
        session.close()

    def draft_bug_report(self, plan_id: int, test_case: dict, error_message: str):
        title = test_case.get('title', 'Unknown')
        steps = test_case.get('steps', [])
        failing_selector = steps[-1].get('selector', 'N/A') if steps else 'N/A'
        history_text = self._get_history(failing_selector)
        response = self.chain.invoke({
            "pattern_context": history_text,
            "title": title,
            "steps_text": str(steps),
            "error_message": error_message
        })
        self.log_failure(plan_id, failing_selector, error_message)
        return response.content if hasattr(response, 'content') else str(response)

    def process_failure(self, plan_id, test_case, error_message, screenshot_path=None):
        report_content = self.draft_bug_report(plan_id, test_case, error_message)
        summary = f"[UI FAILURE] - {test_case.get('title')}"
        jira_key = self.jira_client.create_bug(summary, report_content)
        if jira_key and screenshot_path:
            self.jira_client.attach_file(jira_key, screenshot_path)
        return jira_key
