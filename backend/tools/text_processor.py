import re
from typing import Optional

from tools.base import BaseTool, ToolResult

_OPERATIONS = {
    "uppercase": lambda s: s.upper(),
    "upper case": lambda s: s.upper(),
    "lowercase": lambda s: s.lower(),
    "lower case": lambda s: s.lower(),
    "title case": lambda s: s.title(),
    "capitalize": lambda s: s.capitalize(),
    "reverse": lambda s: s[::-1],
    "word count": lambda s: str(len(s.split())),
    "character count": lambda s: str(len(s)),
    "char count": lambda s: str(len(s)),
    "trim": lambda s: s.strip(),
}

# Words stripped out when we fall back to inferring the target text from
# the raw task instead of finding it in quotes or after a colon.
_INSTRUCTION_WORDS_RE = re.compile(
    r"\b(convert|to|the|please|make|this|text|string|into|of)\b", re.IGNORECASE
)


class TextProcessorTool(BaseTool):
    name = "TextProcessorTool"
    description = (
        "Transforms text: uppercase, lowercase, title case, capitalize, reverse, "
        "word count, character count, trim."
    )

    def can_handle(self, task: str) -> bool:
        # Acts as a catch-all fallback for plain text input (always True so
        # Calculator and Weather, which appear earlier in the tool list, take
        # priority for their own inputs).
        return bool(task.strip())

    def execute(self, task: str) -> ToolResult:
        lowered = task.lower()
        matched_keyword = next((k for k in _OPERATIONS if k in lowered), None)
        if matched_keyword is None:
            # No explicit operation requested — default to uppercase.
            return ToolResult(success=True, output=task.upper())

        target_text = self._extract_target_text(task, matched_keyword)
        if not target_text:
            return ToolResult(success=False, output=None, error="No text found to process")

        try:
            result = _OPERATIONS[matched_keyword](target_text)
            return ToolResult(success=True, output=result)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, output=None, error=str(exc))

    @staticmethod
    def _extract_target_text(task: str, keyword: str) -> Optional[str]:
        # 1. Prefer quoted text: convert 'hello world' to uppercase
        quoted = re.search(r"['\"]([^'\"]+)['\"]", task)
        if quoted:
            return quoted.group(1)

        # 2. Text after a colon: uppercase: hello world
        if ":" in task:
            after_colon = task.split(":", 1)[1].strip()
            if after_colon:
                return after_colon

        # 3. Text immediately after the matched keyword
        lowered = task.lower()
        idx = lowered.find(keyword)
        after_keyword = task[idx + len(keyword):].strip()
        after_keyword = re.sub(r"^(the\s+)?(text|string|input)?[:\s]*", "", after_keyword, flags=re.IGNORECASE)
        if after_keyword:
            return after_keyword

        # 4. Last resort: strip instruction words and the keyword itself
        cleaned = _INSTRUCTION_WORDS_RE.sub("", task)
        cleaned = re.sub(re.escape(keyword), "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned or None
