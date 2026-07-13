import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.controller import AgentController


class TestAgentController:
    def setup_method(self):
        self.agent = AgentController()

    def test_selects_calculator_tool(self):
        record = self.agent.run("What is 3 + 5?")
        assert "CalculatorTool" in record.tools_used
        assert record.final_output == "8"

    def test_selects_text_processor_tool(self):
        record = self.agent.run("Convert to uppercase: hello world")
        assert "TextProcessorTool" in record.tools_used
        assert record.final_output == "HELLO WORLD"

    def test_selects_weather_tool(self):
        record = self.agent.run("What's the weather in Chicago?")
        assert "WeatherMockTool" in record.tools_used

    def test_trace_has_expected_shape(self):
        record = self.agent.run("3 + 5")
        descriptions = [s.description for s in record.steps]
        assert descriptions[0].startswith("Received input")
        assert any("Selected tool" in d for d in descriptions)
        assert any("Tool result" in d for d in descriptions)
        assert descriptions[-1] == "Returning result to user"

    def test_plain_text_falls_back_to_uppercase(self):
        # TextProcessorTool is the catch-all: plain text gets uppercased.
        record = self.agent.run("Tell me a joke")
        assert record.tools_used == ["TextProcessorTool"]
        assert record.final_output == "TELL ME A JOKE"
        assert record.error is None

    def test_multi_step_task(self):
        record = self.agent.run("Calculate 3 + 5 then convert to uppercase: done")
        assert "CalculatorTool" in record.tools_used
        assert "TextProcessorTool" in record.tools_used
        assert len(record.tools_used) == 2

    def test_output_chaining_pipes_prior_result(self):
        # "the result" in step 2 should be substituted with step 1's output.
        record = self.agent.run("Calculate 3 + 5 then uppercase the result")
        assert record.tools_used == ["CalculatorTool", "TextProcessorTool"]
        assert record.final_output == "8"  # uppercase of "8" is still "8"
        descriptions = [s.description for s in record.steps]
        assert any("Chaining prior output" in d for d in descriptions)

    def test_output_chaining_weather_then_uppercase(self):
        record = self.agent.run("weather in Chicago then uppercase the result")
        assert record.tools_used == ["WeatherMockTool", "TextProcessorTool"]
        assert record.final_output == record.final_output.upper()  # last output is uppercased

    def test_step_numbers_are_sequential(self):
        record = self.agent.run("weather in Boston")
        numbers = [s.step_number for s in record.steps]
        assert numbers == list(range(1, len(numbers) + 1))
