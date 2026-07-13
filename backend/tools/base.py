from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolResult:
    """Uniform return type for every tool, so the agent never has to
    special-case a specific tool's output shape."""

    success: bool
    output: Any
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class all tools must implement.

    To add a new tool: subclass BaseTool, implement can_handle() and
    execute(), then register an instance in AgentController's tool list
    (agent/controller.py). Nothing else needs to change - this is what
    keeps the agent/tool layer extensible.
    """

    name: str = "BaseTool"
    description: str = "Base tool"

    @abstractmethod
    def can_handle(self, task: str) -> bool:
        """Return True if this tool can process the given task string."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, task: str) -> ToolResult:
        """Run the tool against the task and return a ToolResult."""
        raise NotImplementedError
