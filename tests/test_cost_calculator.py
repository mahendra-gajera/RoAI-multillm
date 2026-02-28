"""
Unit tests for Cost Calculator
"""
import pytest
from app.utils.cost_calculator import CostCalculator


class TestCostCalculator:
    """Test suite for cost tracking and calculation"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance for testing"""
        return CostCalculator()

    def test_openai_cost_calculation(self, calculator):
        """Test: OpenAI cost calculation with known values"""
        # GPT-4o-mini: $0.15/1M input, $0.6/1M output
        input_tokens = 1000
        output_tokens = 500

        cost = calculator.calculate_openai_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="gpt-4o-mini"
        )

        # Expected: (1000 * 0.15 + 500 * 0.6) / 1,000,000
        expected_cost = (1000 * 0.15 + 500 * 0.6) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001  # Float precision

    def test_openai_gpt4o_cost_higher_than_mini(self, calculator):
        """Test: GPT-4o should cost more than GPT-4o-mini"""
        tokens_in = 10000
        tokens_out = 5000

        cost_mini = calculator.calculate_openai_cost(tokens_in, tokens_out, "gpt-4o-mini")
        cost_4o = calculator.calculate_openai_cost(tokens_in, tokens_out, "gpt-4o")

        assert cost_4o > cost_mini
        # GPT-4o is ~16x more expensive
        assert cost_4o > cost_mini * 10

    def test_gemini_cost_calculation(self, calculator):
        """Test: Gemini cost calculation with known values"""
        # Gemini 2.0 Flash: $0.075/1M input, $0.3/1M output
        input_tokens = 2000
        output_tokens = 1000

        cost = calculator.calculate_gemini_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="gemini-2.0-flash"
        )

        # Expected: (2000 * 0.075 + 1000 * 0.3) / 1,000,000
        expected_cost = (2000 * 0.075 + 1000 * 0.3) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_gemini_cost_calculation_flash(self, calculator):
        """Test: Gemini Flash cost calculation"""
        cost = calculator.calculate_gemini_cost(
            input_tokens=10000,
            output_tokens=5000,
            model="gemini-2.0-flash"
        )

        # Gemini Flash has pricing
        assert cost > 0.0

    def test_cost_comparison_between_models(self, calculator):
        """Test: Compare costs across different models"""
        tokens_in = 10000
        tokens_out = 5000

        costs = {
            "gpt-4o-mini": calculator.calculate_openai_cost(tokens_in, tokens_out, "gpt-4o-mini"),
            "gpt-4o": calculator.calculate_openai_cost(tokens_in, tokens_out, "gpt-4o"),
            "gemini-flash": calculator.calculate_gemini_cost(tokens_in, tokens_out, "gemini-2.0-flash")
        }

        # Gemini Flash should be cheapest
        assert costs["gemini-flash"] == min(costs.values())

        # GPT-4o should be most expensive
        assert costs["gpt-4o"] == max(costs.values())

    def test_zero_tokens_zero_cost(self, calculator):
        """Test: Zero tokens should result in zero cost"""
        cost = calculator.calculate_openai_cost(0, 0, "gpt-4o-mini")
        assert cost == 0.0

    def test_session_cost_tracking(self, calculator):
        """Test: Session cost accumulation"""
        calculator.reset_session()
        initial_total = calculator.get_session_cost()

        # Track some costs
        calculator.track_session_cost("openai", 0.003)
        calculator.track_session_cost("gemini", 0.005)

        total = calculator.get_session_cost()
        assert abs(total - 0.008) < 0.0001

    def test_cost_breakdown_by_provider(self, calculator):
        """Test: Cost breakdown tracks per provider"""
        calculator.reset_session()

        calculator.track_session_cost("openai", 0.010)
        calculator.track_session_cost("gemini", 0.005)
        calculator.track_session_cost("openai", 0.003)

        breakdown = calculator.get_cost_breakdown()

        assert abs(breakdown["openai"] - 0.013) < 0.0001
        assert abs(breakdown["gemini"] - 0.005) < 0.0001
        assert abs(breakdown["total"] - 0.018) < 0.0001
