import hashlib
import re
from datetime import datetime, timezone

from tools.base import BaseTool, ToolResult

_CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Thunderstorms", "Snow", "Windy", "Clear"]

_WEATHER_TRIGGER_RE = re.compile(r"weather", re.IGNORECASE)
# "weather in Chicago" / "weather Chicago"
_CITY_AFTER_RE = re.compile(r"weather\s*(?:in|for|at)?\s*([A-Za-z\s]+?)(?:[?.!]|$)", re.IGNORECASE)
# "Chicago weather" / "chi weather"
_CITY_BEFORE_RE = re.compile(r"([A-Za-z\s]+?)\s*weather", re.IGNORECASE)


class WeatherMockTool(BaseTool):
    name = "WeatherMockTool"
    description = "Returns a deterministic mock weather report for a given city (no external API call)."

    def can_handle(self, task: str) -> bool:
        return bool(_WEATHER_TRIGGER_RE.search(task))

    def execute(self, task: str) -> ToolResult:
        city = self._extract_city(task)
        if not city:
            return ToolResult(success=False, output=None, error="No city found in task")

        # Deterministic pseudo-random values derived from the city name, so
        # the same city always returns the same mock report within a run.
        seed = int(hashlib.sha256(city.lower().encode()).hexdigest(), 16)
        temp_f = 40 + (seed % 60)
        condition = _CONDITIONS[seed % len(_CONDITIONS)]
        humidity = 30 + (seed % 60)

        summary = f"{city}: {temp_f}\u00b0F, {condition}, {humidity}% humidity"
        return ToolResult(success=True, output=summary)

    @staticmethod
    def _extract_city(task: str) -> str:
        # Try "weather [in] City" first, then "City weather"
        match = _CITY_AFTER_RE.search(task) or _CITY_BEFORE_RE.search(task)
        if not match:
            return ""
        city = match.group(1).strip()
        city = re.sub(r"^(the\s+)", "", city, flags=re.IGNORECASE)
        return city.title()
