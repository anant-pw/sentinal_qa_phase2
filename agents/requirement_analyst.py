import requests
import yaml
import re
from core.ai_factory import AIFactory
from loguru import logger

# [INFRASTRUCTURE] Endpoint for the Sentinel-QA FastAPI Service
API_URL = "http://localhost:8000/plans"

class RequirementAnalyst:
    def __init__(self):
        # Initializes SambaNova/Groq via the Factory
        self.llm = AIFactory.get_model()

    def submit_to_api(self, title: str, steps: list):
        """POST structured test plan to FastAPI for DB persistence."""
        payload = {"title": title, "steps": steps}
        try:
            # Pydantic in FastAPI will validate this schema automatically
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                logger.success(f"✅ AI Plan stored in DB via API: {title}")
            else:
                logger.error(f"❌ API Rejected Plan: {response.text}")
        except Exception as e:
            logger.error(f"❌ Connection to Sentinel API failed: {e}")

    def generate_test_plan(self, requirement_text: str):
        """Converts raw text to JSON and submits to the Sentinel ecosystem."""
        
        # 1. Context Injection (From config.yaml)
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        base_url = config.get("base_url")

        # 2. Architect the Prompt (Optimized for Llama-3.3-70B)
        prompt = f"""
        You are a Senior QA Architect. Convert this requirement into a JSON test plan.
        
        REQUIREMENT: {requirement_text}
        
        STRICT SELECTOR GUIDELINES (OrangeHRM):
        - Username field: input[name="username"]
        - Password field: input[name="password"]
        - Login Button: button[type="submit"]
        - Dashboard Header: .oxd-topbar-header-breadcrumb
        
        STRICT RULES:
        1. The first step MUST be: action: "navigate", data: "{base_url}"
        2. Return ONLY JSON. No introductory text. No markdown backticks.
        3. Keys required: "title" (string) and "steps" (list of objects).
        4. Step object format: {{"action": str, "selector": str, "data": str}}
        5. Valid Actions: navigate, type, click, verify_text.
        """
        
        logger.info("🧠 Invoking SambaNova for Requirement Analysis...")
        
        # 3. AI Execution
        response = self.llm.invoke(prompt)
        raw_text = response.content if hasattr(response, 'content') else str(response)

        # 4. Self-Healing Parser
        # Removes common AI formatting like ```json ... ```
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        
        try:
            # We use yaml.safe_load as it is a superset of JSON
            parsed_data = yaml.safe_load(clean_json)
            
            # 5. DB Persistence via API
            self.submit_to_api(
                title=parsed_data.get('title', 'Untitled AI Test'),
                steps=parsed_data.get('steps', [])
            )
            
        except Exception as e:
            logger.error(f"❌ AI hallucinated invalid JSON: {e}")
            logger.debug(f"Raw Output: {clean_json}")

if __name__ == "__main__":
    analyst = RequirementAnalyst()
    draft = "User logs in with Admin/admin123 and verifies the Dashboard breadcrumb."
    analyst.generate_test_plan(draft)