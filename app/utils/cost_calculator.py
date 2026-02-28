"""
Cost Calculator - LLM Cost Estimation and Tracking
Supplements LiteLLM automatic tracking with custom calculations
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class CostCalculator:
    """
    Cost calculator for LLM API usage.

    Pricing (per 1M tokens, as of 2026):
    - OpenAI GPT-4o: $2.5 input / $10 output
    - OpenAI GPT-4o-mini: $0.15 input / $0.6 output
    - Gemini 2.0 Flash: $0.075 input / $0.3 output
    - Gemini 2.0 Pro: $1.25 input / $5 output
    """

    def __init__(self):
        """Initialize cost calculator with pricing configuration."""
        # OpenAI pricing (per 1M tokens)
        self.openai_input_cost = float(os.getenv("OPENAI_INPUT_COST", "0.15"))
        self.openai_output_cost = float(os.getenv("OPENAI_OUTPUT_COST", "0.6"))

        # Gemini pricing (per 1M tokens)
        self.gemini_input_cost = float(os.getenv("GEMINI_INPUT_COST", "0.075"))
        self.gemini_output_cost = float(os.getenv("GEMINI_OUTPUT_COST", "0.3"))

        # Session tracking
        self.session_costs = {
            "openai": 0.0,
            "gemini": 0.0,
            "ensemble": 0.0,
            "total": 0.0
        }

    def calculate_openai_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o-mini"
    ) -> float:
        """
        Calculate cost for OpenAI API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (gpt-4o, gpt-4o-mini)

        Returns:
            Total cost in dollars
        """
        # Adjust pricing based on model
        if "gpt-4o" in model and "mini" not in model:
            input_cost = 2.5
            output_cost = 10.0
        else:  # gpt-4o-mini
            input_cost = self.openai_input_cost
            output_cost = self.openai_output_cost

        cost = (
            (input_tokens / 1_000_000) * input_cost +
            (output_tokens / 1_000_000) * output_cost
        )

        return round(cost, 6)

    def calculate_gemini_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-2.0-flash"
    ) -> float:
        """
        Calculate cost for Gemini API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (gemini-2.0-flash, gemini-2.0-pro)

        Returns:
            Total cost in dollars
        """
        # Adjust pricing based on model
        if "pro" in model.lower():
            input_cost = 1.25
            output_cost = 5.0
        else:  # flash
            input_cost = self.gemini_input_cost
            output_cost = self.gemini_output_cost

        cost = (
            (input_tokens / 1_000_000) * input_cost +
            (output_tokens / 1_000_000) * output_cost
        )

        return round(cost, 6)

    def calculate_cost(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        Calculate cost for any provider.

        Args:
            provider: Provider name (openai, gemini)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Optional model name for specific pricing

        Returns:
            Total cost in dollars
        """
        if provider.lower() == "openai":
            return self.calculate_openai_cost(input_tokens, output_tokens, model or "gpt-4o-mini")
        elif provider.lower() == "gemini":
            return self.calculate_gemini_cost(input_tokens, output_tokens, model or "gemini-2.0-flash")
        else:
            return 0.0

    def track_session_cost(
        self,
        provider: str,
        cost: float
    ) -> None:
        """
        Track cost for current session.

        Args:
            provider: Provider name (openai, gemini, ensemble)
            cost: Cost to add
        """
        if provider in self.session_costs:
            self.session_costs[provider] += cost
            self.session_costs["total"] += cost

    def get_session_cost(self, provider: Optional[str] = None) -> float:
        """
        Get session cost.

        Args:
            provider: Optional provider name (returns total if None)

        Returns:
            Session cost in dollars
        """
        if provider is None:
            return round(self.session_costs["total"], 4)
        return round(self.session_costs.get(provider, 0.0), 4)

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get detailed cost breakdown.

        Returns:
            Dictionary with costs by provider
        """
        return {
            provider: round(cost, 4)
            for provider, cost in self.session_costs.items()
        }

    def compare_model_costs(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Compare costs across different models.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with cost comparison
        """
        openai_mini_cost = self.calculate_openai_cost(
            input_tokens, output_tokens, "gpt-4o-mini"
        )
        openai_4o_cost = self.calculate_openai_cost(
            input_tokens, output_tokens, "gpt-4o"
        )
        gemini_flash_cost = self.calculate_gemini_cost(
            input_tokens, output_tokens, "gemini-2.0-flash"
        )
        gemini_pro_cost = self.calculate_gemini_cost(
            input_tokens, output_tokens, "gemini-2.0-pro"
        )

        costs = {
            "gpt-4o-mini": openai_mini_cost,
            "gpt-4o": openai_4o_cost,
            "gemini-2.0-flash": gemini_flash_cost,
            "gemini-2.0-pro": gemini_pro_cost
        }

        cheapest = min(costs.items(), key=lambda x: x[1])
        most_expensive = max(costs.items(), key=lambda x: x[1])

        return {
            "costs": costs,
            "cheapest": {
                "model": cheapest[0],
                "cost": cheapest[1]
            },
            "most_expensive": {
                "model": most_expensive[0],
                "cost": most_expensive[1]
            },
            "savings_vs_most_expensive": {
                model: round(most_expensive[1] - cost, 6)
                for model, cost in costs.items()
            }
        }

    def estimate_monthly_cost(
        self,
        daily_requests: int,
        avg_input_tokens: int,
        avg_output_tokens: int,
        provider: str = "openai",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate monthly cost based on usage patterns.

        Args:
            daily_requests: Average requests per day
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            provider: Provider name
            model: Optional model name

        Returns:
            Dictionary with monthly cost estimate
        """
        cost_per_request = self.calculate_cost(
            provider,
            avg_input_tokens,
            avg_output_tokens,
            model
        )

        daily_cost = cost_per_request * daily_requests
        monthly_cost = daily_cost * 30
        yearly_cost = daily_cost * 365

        return {
            "cost_per_request": round(cost_per_request, 6),
            "daily_cost": round(daily_cost, 2),
            "monthly_cost": round(monthly_cost, 2),
            "yearly_cost": round(yearly_cost, 2),
            "assumptions": {
                "daily_requests": daily_requests,
                "avg_input_tokens": avg_input_tokens,
                "avg_output_tokens": avg_output_tokens,
                "provider": provider,
                "model": model or "default"
            }
        }

    def calculate_savings(
        self,
        actual_cost: float,
        baseline_cost: float
    ) -> Dict[str, Any]:
        """
        Calculate cost savings compared to baseline.

        Args:
            actual_cost: Actual cost with intelligent routing
            baseline_cost: Cost if using single expensive model

        Returns:
            Dictionary with savings analysis
        """
        savings = baseline_cost - actual_cost
        savings_percent = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0

        return {
            "actual_cost": round(actual_cost, 4),
            "baseline_cost": round(baseline_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
            "cost_reduction_ratio": round(actual_cost / baseline_cost, 2) if baseline_cost > 0 else 0.0
        }

    def reset_session(self) -> None:
        """Reset session cost tracking."""
        self.session_costs = {
            "openai": 0.0,
            "gemini": 0.0,
            "ensemble": 0.0,
            "total": 0.0
        }

    def get_pricing_info(self) -> Dict[str, Any]:
        """
        Get current pricing configuration.

        Returns:
            Dictionary with pricing per 1M tokens
        """
        return {
            "openai": {
                "gpt-4o-mini": {
                    "input": self.openai_input_cost,
                    "output": self.openai_output_cost
                },
                "gpt-4o": {
                    "input": 2.5,
                    "output": 10.0
                }
            },
            "gemini": {
                "gemini-2.0-flash": {
                    "input": self.gemini_input_cost,
                    "output": self.gemini_output_cost
                },
                "gemini-2.0-pro": {
                    "input": 1.25,
                    "output": 5.0
                }
            },
            "unit": "USD per 1M tokens"
        }
