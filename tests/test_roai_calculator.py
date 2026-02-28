"""
Unit tests for RoAI Calculator
"""
import pytest
from app.utils.roai_calculator import RoAICalculator


class TestRoAICalculator:
    """Test suite for Return on AI Investment calculations"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance for testing"""
        return RoAICalculator()

    def test_roai_calculation_positive(self, calculator):
        """Test: Positive ROI calculation"""
        # Formula: (fraud_prevented + manual_saved - llm_cost) / llm_cost
        llm_cost = 100.0
        fraud_prevented = 50000.0
        manual_cost_saved = 2000.0

        result = calculator.calculate_roai(
            llm_cost=llm_cost,
            fraud_prevented=fraud_prevented,
            manual_cost_saved=manual_cost_saved
        )

        # Expected: (50000 + 2000 - 100) / 100 = 519
        expected_roai = (fraud_prevented + manual_cost_saved - llm_cost) / llm_cost
        assert isinstance(result, dict)
        assert "roai" in result
        assert abs(result["roai"] - expected_roai) < 0.01

    def test_roai_calculation_with_zero_llm_cost(self, calculator):
        """Test: Zero LLM cost should handle gracefully"""
        result = calculator.calculate_roai(
            llm_cost=0.0,
            fraud_prevented=10000.0,
            manual_cost_saved=1000.0
        )

        assert isinstance(result, dict)
        assert "roai" in result
        # When cost is 0, RoAI is 0 by implementation
        assert result["roai"] == 0.0

    def test_roai_calculation_negative_roi(self, calculator):
        """Test: Negative ROI when costs exceed benefits"""
        llm_cost = 10000.0
        fraud_prevented = 5000.0
        manual_cost_saved = 1000.0

        result = calculator.calculate_roai(
            llm_cost=llm_cost,
            fraud_prevented=fraud_prevented,
            manual_cost_saved=manual_cost_saved
        )

        # Expected: (5000 + 1000 - 10000) / 10000 = -0.4
        expected_roai = (fraud_prevented + manual_cost_saved - llm_cost) / llm_cost
        assert isinstance(result, dict)
        assert abs(result["roai"] - expected_roai) < 0.01
        assert result["roai"] < 0  # Negative ROI

    def test_roai_breakeven_scenario(self, calculator):
        """Test: Break-even when benefits equal costs"""
        llm_cost = 1000.0
        fraud_prevented = 800.0
        manual_cost_saved = 200.0

        result = calculator.calculate_roai(
            llm_cost=llm_cost,
            fraud_prevented=fraud_prevented,
            manual_cost_saved=manual_cost_saved
        )

        # (800 + 200 - 1000) / 1000 = 0
        assert isinstance(result, dict)
        assert abs(result["roai"] - 0.0) < 0.01

    def test_roai_high_fraud_prevention_value(self, calculator):
        """Test: High ROI with significant fraud prevention"""
        llm_cost = 100.0
        fraud_prevented = 100000.0
        manual_cost_saved = 5000.0

        result = calculator.calculate_roai(
            llm_cost=llm_cost,
            fraud_prevented=fraud_prevented,
            manual_cost_saved=manual_cost_saved
        )

        # Should be very high ROI
        assert isinstance(result, dict)
        assert result["roai"] > 1000

    def test_roai_with_metadata(self, calculator):
        """Test: Calculate RoAI returns complete metadata"""
        result = calculator.calculate_roai(
            llm_cost=500.0,
            fraud_prevented=25000.0,
            manual_cost_saved=3000.0
        )

        assert "roai" in result
        assert "total_value_generated" in result
        assert "net_value" in result
        assert result["roai"] > 0
        assert result["total_value_generated"] == 28000.0
        assert result["net_value"] == 27500.0

    def test_roai_comparison_scenarios(self, calculator):
        """Test: Compare different scenarios"""
        scenarios = [
            {"name": "Conservative", "llm_cost": 100, "fraud": 5000, "manual": 500},
            {"name": "Aggressive", "llm_cost": 100, "fraud": 50000, "manual": 2000},
            {"name": "Moderate", "llm_cost": 100, "fraud": 10000, "manual": 1000}
        ]

        results = []
        for scenario in scenarios:
            result = calculator.calculate_roai(
                llm_cost=scenario["llm_cost"],
                fraud_prevented=scenario["fraud"],
                manual_cost_saved=scenario["manual"]
            )
            results.append({"name": scenario["name"], "roai": result["roai"]})

        # Aggressive should have highest ROI
        aggressive = next(r for r in results if r["name"] == "Aggressive")
        conservative = next(r for r in results if r["name"] == "Conservative")

        assert aggressive["roai"] > conservative["roai"]
