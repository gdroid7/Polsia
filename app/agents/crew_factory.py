"""Agent factory — maps agent_type strings to agent classes and runs them."""
import importlib

AGENT_MAP: dict[str, tuple[str, str]] = {
    "orchestrator": ("app.agents.orchestrator.agent", "OrchestratorAgent"),
    "social_media": ("app.agents.social_media.agent", "SocialMediaAgent"),
    "competitor_research": ("app.agents.competitor_research.agent", "CompetitorResearchAgent"),
    "business_planning": ("app.agents.business_planning.agent", "BusinessPlanningAgent"),
    "email_outreach": ("app.agents.email_outreach.agent", "EmailOutreachAgent"),
    "customer_support": ("app.agents.customer_support.agent", "CustomerSupportAgent"),
    "ads_management": ("app.agents.ads_management.agent", "AdsManagementAgent"),
    "code_generation": ("app.agents.code_generation.agent", "CodeGenerationAgent"),
    "finance": ("app.agents.finance.agent", "FinanceAgent"),
}


def run_agent_for_task(agent_type: str, task: dict, context: dict) -> dict:
    """Instantiate the correct agent for agent_type and run it."""
    if agent_type not in AGENT_MAP:
        raise ValueError(f"Unknown agent type: {agent_type}")
    module_path, class_name = AGENT_MAP[agent_type]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    agent = cls()
    return agent.timed_run(task, context)
