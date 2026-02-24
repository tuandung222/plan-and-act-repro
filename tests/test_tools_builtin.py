from __future__ import annotations

from plan_and_act.tools.calc import CalculatorTool
from plan_and_act.tools.web import parse_duckduckgo_results


def test_calculator_tool_evaluates_expression() -> None:
    tool = CalculatorTool()
    out = tool.run({"expression": "sqrt(144) + 2**5 - 3"})

    assert out["ok"] is True
    assert out["result"] == 41.0


def test_calculator_tool_rejects_unsafe_expression() -> None:
    tool = CalculatorTool()
    out = tool.run({"expression": "__import__('os').system('whoami')"})

    assert out["ok"] is False


def test_parse_duckduckgo_results_extracts_links() -> None:
    sample = '''
    <html><body>
      <a class="result__a" href="https://example.com/a">Result A</a>
      <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fb">Result B</a>
    </body></html>
    '''

    out = parse_duckduckgo_results(sample, max_results=5)
    assert len(out) == 2
    assert out[0]["url"] == "https://example.com/a"
    assert out[1]["url"] == "https://example.org/b"
