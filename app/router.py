"""
LLM Router - Intelligent Model Selection
Routes tasks to optimal LLM based on task characteristics
"""

import os
from typing import Tuple
from app.models.task import Task
from dotenv import load_dotenv

load_dotenv()


class LLMRouter:
    """
    Intelligent router that selects the optimal LLM for each task.

    Routing Logic:
    1. Strict JSON requirement → OpenAI (best structured output support)
    2. Large context (>80k tokens) → Gemini (long-context capability)
    3. Multi-document analysis → Gemini (better for complex correlation)
    4. High business impact (>0.8) → Ensemble (dual validation)
    5. Default → OpenAI (general purpose)
    """

    def __init__(self):
        """Initialize router with configuration thresholds."""
        self.context_length_threshold = int(
            os.getenv("CONTEXT_LENGTH_THRESHOLD", "80000")
        )
        self.business_impact_threshold = float(
            os.getenv("BUSINESS_IMPACT_THRESHOLD", "0.8")
        )

    def route(self, task: Task) -> str:
        """
        Determine the optimal LLM for the given task.

        Args:
            task: Task object with routing attributes

        Returns:
            Model selection: "openai", "gemini", or "ensemble"
        """
        # Priority 1: Strict JSON requirement → OpenAI
        if task.requires_strict_json:
            return "openai"

        # Priority 2: Large context → Gemini
        if task.context_length > self.context_length_threshold:
            return "gemini"

        # Priority 3: Multi-document analysis → Gemini
        if task.multi_document:
            return "gemini"

        # Priority 4: High business impact → Ensemble
        if task.business_impact > self.business_impact_threshold:
            return "ensemble"

        # Default: OpenAI for general tasks
        return "openai"

    def get_routing_reason(self, task: Task) -> str:
        """
        Get human-readable explanation for routing decision.

        Args:
            task: Task object

        Returns:
            Explanation string describing why this model was selected
        """
        # Check conditions in priority order
        if task.requires_strict_json:
            return "Structured JSON output required - OpenAI provides best schema adherence"

        if task.context_length > self.context_length_threshold:
            return f"Large context ({task.context_length:,} tokens) - Gemini optimized for long-context processing"

        if task.multi_document:
            return "Multi-document analysis - Gemini excels at cross-document correlation"

        if task.business_impact > self.business_impact_threshold:
            return f"High business impact ({task.business_impact:.1%}) - Ensemble validation for critical decisions"

        return "General task - OpenAI provides optimal balance of speed, cost, and quality"

    def get_routing_details(self, task: Task) -> dict:
        """
        Get detailed routing information including decision and reasoning.

        Args:
            task: Task object

        Returns:
            Dictionary with model selection and detailed routing information
        """
        selected_model = self.route(task)
        reason = self.get_routing_reason(task)

        return {
            "selected_model": selected_model,
            "reason": reason,
            "task_characteristics": {
                "requires_strict_json": task.requires_strict_json,
                "context_length": task.context_length,
                "multi_document": task.multi_document,
                "business_impact": task.business_impact,
                "task_type": task.task_type
            },
            "thresholds": {
                "context_length_threshold": self.context_length_threshold,
                "business_impact_threshold": self.business_impact_threshold
            }
        }

    def estimate_cost_savings(self, task: Task) -> dict:
        """
        Estimate cost savings vs. always using most expensive model.

        Args:
            task: Task object

        Returns:
            Dictionary with cost comparison and savings estimate
        """
        selected_model = self.route(task)

        # Approximate cost per 1M tokens (input + output blended)
        cost_per_million = {
            "openai": 0.375,  # gpt-4o-mini average
            "gemini": 0.1875,  # gemini-2.0-flash average
            "gpt-4o": 6.25,  # expensive baseline
        }

        # Estimate tokens (input + output)
        estimated_tokens = task.context_length + 500  # assume 500 output tokens

        # Calculate costs
        selected_cost = (estimated_tokens / 1_000_000) * cost_per_million.get(
            selected_model.split("_")[0], cost_per_million["openai"]
        )

        baseline_cost = (estimated_tokens / 1_000_000) * cost_per_million["gpt-4o"]

        savings = baseline_cost - selected_cost
        savings_percent = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

        return {
            "selected_model": selected_model,
            "selected_cost": selected_cost,
            "baseline_cost": baseline_cost,
            "savings": savings,
            "savings_percent": savings_percent,
            "estimated_tokens": estimated_tokens
        }

    def validate_routing_decision(self, task: Task, expected_model: str) -> bool:
        """
        Validate that routing decision matches expected model (for testing).

        Args:
            task: Task object
            expected_model: Expected model selection

        Returns:
            True if routing matches expected model
        """
        actual_model = self.route(task)
        return actual_model == expected_model
