import re
from datetime import datetime, timezone
from typing import List, Optional

from models import ExecutionStep, TaskRecord
from tools.base import BaseTool
from tools.calculator import CalculatorTool
from tools.text_processor import TextProcessorTool
from tools.weather_mock import WeatherMockTool

# Splits a task into ordered sub-tasks on explicit sequencing language,
# e.g. "calculate 3 + 5 then convert the result to uppercase".
_SPLIT_RE = re.compile(r"\s+(?:and then|then)\s+", re.IGNORECASE)

# Phrases in a later segment that refer back to the prior step's output.
_RESULT_REF_RE = re.compile(r'\b(the result|the output|it|that)\b', re.IGNORECASE)


class AgentController:
    """Parses a task, selects the right tool(s), executes them, and returns
    a structured execution trace alongside the final output.

    Tool selection is a simple ordered pipeline: tools are tried in
    self.tools order and the first one whose can_handle() returns True
    wins for a given segment. This is intentionally simple (regex /
    keyword based rather than an LLM call) so behavior is deterministic
    and easy to test - but it mirrors the shape of a real agent loop:
    parse -> select tool -> execute -> observe -> respond.

    Extensibility: adding a new tool means implementing BaseTool and
    appending an instance to self.tools. No other agent code changes.
    """

    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools = tools or [CalculatorTool(), WeatherMockTool(), TextProcessorTool()]

    def run(self, task: str) -> TaskRecord:
        steps: List[ExecutionStep] = []
        tools_used: List[str] = []
        outputs: List[str] = []
        step_num = 1

        steps.append(ExecutionStep(step_number=step_num, description=f'Received input "{task}"'))
        step_num += 1

        segments = self._split_task(task)
        if len(segments) > 1:
            steps.append(
                ExecutionStep(
                    step_number=step_num,
                    description=f"Detected {len(segments)} sub-tasks: {segments}",
                )
            )
            step_num += 1

        overall_error = None
        last_output: Optional[str] = None
        chained = False
        for segment in segments:
            effective_segment = segment
            if last_output is not None:
                if _RESULT_REF_RE.search(segment):
                    # Explicit back-reference: substitute it.
                    effective_segment = _RESULT_REF_RE.sub(f'"{last_output}"', segment)
                    chained = True
                    steps.append(
                        ExecutionStep(
                            step_number=step_num,
                            description=f'Chaining prior output — resolved segment: "{effective_segment}"',
                        )
                    )
                    step_num += 1
                elif not any(t.can_handle(segment) for t in self.tools[:-1]):
                    # No explicit reference, but only the catch-all tool would handle
                    # this segment — implicitly treat prior output as the input.
                    effective_segment = f'{segment}: "{last_output}"'
                    chained = True
                    steps.append(
                        ExecutionStep(
                            step_number=step_num,
                            description=f'Implicitly chaining prior output — resolved segment: "{effective_segment}"',
                        )
                    )
                    step_num += 1

            tool = self._select_tool(effective_segment)

            if tool is None:
                steps.append(
                    ExecutionStep(step_number=step_num, description=f'No matching tool found for: "{effective_segment}"')
                )
                step_num += 1
                overall_error = overall_error or f'No tool could handle: "{effective_segment}"'
                last_output = None
                continue

            steps.append(ExecutionStep(step_number=step_num, description=f"Selected tool: {tool.name}"))
            step_num += 1

            result = tool.execute(effective_segment)

            if not result.success:
                steps.append(ExecutionStep(step_number=step_num, description=f"Tool error: {result.error}"))
                step_num += 1
                overall_error = overall_error or result.error
                last_output = None
                continue

            steps.append(ExecutionStep(step_number=step_num, description=f"Tool result: {result.output}"))
            step_num += 1
            tools_used.append(tool.name)
            outputs.append(str(result.output))
            last_output = str(result.output)

        steps.append(ExecutionStep(step_number=step_num, description="Returning result to user"))

        if not outputs:
            final_output = "Sorry, I couldn't find a tool to handle this task."
        elif chained:
            final_output = outputs[-1]
        else:
            final_output = " | ".join(outputs)

        return TaskRecord(
            task=task,
            final_output=final_output,
            steps=steps,
            tools_used=tools_used,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=overall_error,
        )

    def _select_tool(self, segment: str) -> Optional[BaseTool]:
        for tool in self.tools:
            if tool.can_handle(segment):
                return tool
        return None

    @staticmethod
    def _split_task(task: str) -> List[str]:
        parts = [p.strip() for p in _SPLIT_RE.split(task) if p.strip()]
        return parts if parts else [task.strip()]
