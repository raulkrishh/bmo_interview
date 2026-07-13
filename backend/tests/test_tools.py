import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.calculator import CalculatorTool
from tools.text_processor import TextProcessorTool
from tools.weather_mock import WeatherMockTool


class TestCalculatorTool:
    def setup_method(self):
        self.tool = CalculatorTool()

    def test_can_handle_simple_expression(self):
        assert self.tool.can_handle("What is 3 + 5?")

    def test_can_handle_rejects_no_math(self):
        assert not self.tool.can_handle("Convert this to uppercase")

    def test_execute_addition(self):
        result = self.tool.execute("Calculate 3 + 5")
        assert result.success
        assert result.output == 8

    def test_execute_with_parentheses(self):
        result = self.tool.execute("Compute 2 * (3 + 4)")
        assert result.success
        assert result.output == 14

    def test_execute_division(self):
        result = self.tool.execute("10 / 4")
        assert result.success
        assert result.output == 2.5

    def test_division_by_zero(self):
        result = self.tool.execute("5 / 0")
        assert not result.success
        assert "zero" in result.error.lower()

    def test_no_expression_found(self):
        result = self.tool.execute("no math here")
        assert not result.success


class TestTextProcessorTool:
    def setup_method(self):
        self.tool = TextProcessorTool()

    def test_can_handle_uppercase(self):
        assert self.tool.can_handle("Convert to uppercase: hello world")

    def test_can_handle_plain_text_fallback(self):
        # TextProcessorTool is the catch-all: handles any non-empty string.
        assert self.tool.can_handle("weather in Chicago")
        assert self.tool.can_handle("hello world")

    def test_plain_text_defaults_to_uppercase(self):
        result = self.tool.execute("hello world")
        assert result.success
        assert result.output == "HELLO WORLD"

    def test_uppercase_with_colon(self):
        result = self.tool.execute("Convert to uppercase: hello world")
        assert result.success
        assert result.output == "HELLO WORLD"

    def test_uppercase_with_quotes(self):
        result = self.tool.execute('Convert "hello world" to uppercase')
        assert result.success
        assert result.output == "HELLO WORLD"

    def test_lowercase(self):
        result = self.tool.execute("Make 'HELLO' lowercase")
        assert result.success
        assert result.output == "hello"

    def test_word_count(self):
        result = self.tool.execute("word count: the quick brown fox")
        assert result.success
        assert result.output == "4"

    def test_reverse(self):
        result = self.tool.execute("reverse: abc")
        assert result.success
        assert result.output == "cba"


class TestWeatherMockTool:
    def setup_method(self):
        self.tool = WeatherMockTool()

    def test_can_handle_weather_query(self):
        assert self.tool.can_handle("What's the weather in Chicago?")

    def test_can_handle_rejects_unrelated(self):
        assert not self.tool.can_handle("3 + 5")

    def test_execute_extracts_city(self):
        result = self.tool.execute("weather in Chicago")
        assert result.success
        assert "Chicago" in result.output

    def test_deterministic_output(self):
        r1 = self.tool.execute("weather in Boston")
        r2 = self.tool.execute("weather in Boston")
        assert r1.output == r2.output
