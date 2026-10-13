"""Finance agent — revenue tracking, Stripe events, and expense management."""
from app.agents.base_agent import BasePolsiaAgent
from app.services.company_service import build_context_prompt


class FinanceAgent(BasePolsiaAgent):
    agent_type = "finance"

    def run(self, task: dict, context: dict) -> dict:
        context_str = build_context_prompt(context)
        prompt = f"""You are the Finance agent for a company.
Task: {task.get('title', 'No title')}
Description: {task.get('description', 'No description')}

Company context:
{context_str}

Respond with a JSON object containing:
- "summary": one-sentence summary of what you did
- "result": detailed output of the task
"""
        try:
            result = self.call_claude_json(prompt)
        except Exception as e:
            result = {"summary": f"Task failed: {e}", "result": {}}

        return {
            "summary": result.get("summary", str(result)),
            "result": result,
        }
