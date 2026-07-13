from typing import List, Optional

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Incoming request body for POST /api/tasks."""

    task: str = Field(..., min_length=1, description="Natural language task to process")


class ExecutionStep(BaseModel):
    """A single step in the agent's execution trace."""

    step_number: int
    description: str


class TaskRecord(BaseModel):
    """A fully-processed task: input, output, trace, and metadata."""

    id: str = ""
    task: str
    final_output: str
    steps: List[ExecutionStep]
    tools_used: List[str]
    timestamp: str
    error: Optional[str] = None
