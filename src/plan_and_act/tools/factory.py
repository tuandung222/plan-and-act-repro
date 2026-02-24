from __future__ import annotations

from plan_and_act.tools.base import ToolRegistry
from plan_and_act.tools.calc import CalculatorTool
from plan_and_act.tools.github import GitHubTopContributorTool
from plan_and_act.tools.web import FetchURLTool, WebSearchTool


def build_default_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        tools={
            WebSearchTool.name: WebSearchTool(),
            FetchURLTool.name: FetchURLTool(),
            CalculatorTool.name: CalculatorTool(),
            GitHubTopContributorTool.name: GitHubTopContributorTool(),
        }
    )
