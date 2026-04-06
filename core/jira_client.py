import os
from atlassian import Jira
from loguru import logger

class JiraClient:
    def __init__(self):
        # Initializes Jira Cloud connection using .env credentials
        self.jira = Jira(
            url=os.getenv("JIRA_URL"),
            username=os.getenv("JIRA_EMAIL"),
            password=os.getenv("JIRA_API_TOKEN"),
            cloud=True
        )
        self.project_key = os.getenv("JIRA_PROJECT_KEY")

    def create_bug(self, summary: str, description: str):
        """Creates a ticket in Jira using the configured project and issue type."""
        issue_type = os.getenv("JIRA_ISSUE_TYPE", "Bug") 
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'labels': ['Sentinel-QA', 'AI-Generated']
            }
            new_issue = self.jira.create_issue(fields=issue_dict)
            logger.success(f"🎫 Jira Bug Created: {new_issue['key']}")
            return new_issue['key']
        except Exception as e:
            logger.error(f"❌ Failed to create Jira issue: {e}")
            return None

    def attach_file(self, issue_key: str, file_path: str):
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"⚠️ Screenshot file not found: {file_path}")
            return
        try:
            self.jira.add_attachment(issue_key=issue_key, filename=file_path)
            logger.success(f"🖼️ Screenshot attached to {issue_key}")
        except Exception as e:
            logger.error(f"❌ Failed to attach: {type(e).__name__}: {e}")