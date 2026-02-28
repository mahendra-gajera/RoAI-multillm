"""
Ensemble Service - Dual Model Validation
Runs parallel analysis with OpenAI and Gemini for high-risk decisions
"""

import asyncio
import os
from typing import Dict, Any, Tuple
from app.models.task import Task
from app.gateway import AIGateway
from app.services.openai_service import OpenAIService
from app.services.gemini_service import GeminiService
from dotenv import load_dotenv

load_dotenv()


class EnsembleService:
    """
    Ensemble service for high-risk decision validation.

    Features:
    - Parallel execution of OpenAI and Gemini analysis
    - Result comparison and deviation detection
    - Automatic escalation for high deviation
    - Consensus-based decision making
    """

    def __init__(
        self,
        gateway: AIGateway = None,
        deviation_threshold: float = None
    ):
        """
        Initialize Ensemble service.

        Args:
            gateway: Shared AI Gateway instance
            deviation_threshold: Threshold for score deviation (0-100)
        """
        self.gateway = gateway or AIGateway()
        self.openai_service = OpenAIService(self.gateway)
        self.gemini_service = GeminiService(self.gateway)

        self.deviation_threshold = deviation_threshold or float(
            os.getenv("ENSEMBLE_DEVIATION_THRESHOLD", "15")
        )

        self.metrics = {
            "total_requests": 0,
            "agreements": 0,
            "disagreements": 0,
            "escalations": 0,
            "total_cost": 0.0,
            "total_latency": 0.0
        }

    def analyze_with_validation(self, task: Task) -> Dict[str, Any]:
        """
        Run parallel analysis with both models and validate results.

        Args:
            task: Task object for analysis

        Returns:
            Dictionary with ensemble results, comparison, and decision
        """
        # Run both analyses in parallel using async
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            openai_result, gemini_result = loop.run_until_complete(
                self._parallel_analysis(task)
            )
            loop.close()
        except Exception as e:
            # Fallback to sequential if async fails
            openai_result = self.openai_service.analyze_risk(task)
            gemini_result = self.gemini_service.analyze_long_context(task)

        # Compare results
        comparison = self._compare_results(openai_result, gemini_result)

        # Make decision
        decision = self._make_decision(openai_result, gemini_result, comparison)

        # Update metrics
        self._update_metrics(openai_result, gemini_result, comparison)

        return {
            "ensemble_decision": decision,
            "openai_result": openai_result,
            "gemini_result": gemini_result,
            "comparison": comparison,
            "metadata": {
                "provider": "ensemble",
                "models_used": ["openai", "gemini"],
                "total_cost": (
                    openai_result.get("metadata", {}).get("cost", 0) +
                    gemini_result.get("metadata", {}).get("cost", 0)
                ),
                "total_latency": max(
                    openai_result.get("metadata", {}).get("latency", 0),
                    gemini_result.get("metadata", {}).get("latency", 0)
                )
            }
        }

    async def _parallel_analysis(self, task: Task) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run OpenAI and Gemini analysis in parallel.

        Args:
            task: Task object

        Returns:
            Tuple of (openai_result, gemini_result)
        """
        openai_task = asyncio.create_task(self._async_openai_analysis(task))
        gemini_task = asyncio.create_task(self._async_gemini_analysis(task))

        openai_result = await openai_task
        gemini_result = await gemini_task

        return openai_result, gemini_result

    async def _async_openai_analysis(self, task: Task) -> Dict[str, Any]:
        """Async wrapper for OpenAI analysis."""
        # Use synchronous call since OpenAIService uses sync methods
        return self.openai_service.analyze_risk(task)

    async def _async_gemini_analysis(self, task: Task) -> Dict[str, Any]:
        """Async wrapper for Gemini analysis."""
        # Use synchronous call since GeminiService uses sync methods
        return self.gemini_service.analyze_long_context(task)

    def _compare_results(
        self,
        openai_result: Dict[str, Any],
        gemini_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare results from both models.

        Args:
            openai_result: OpenAI analysis result
            gemini_result: Gemini analysis result

        Returns:
            Dictionary with comparison metrics
        """
        # Extract risk scores
        openai_score = openai_result.get("risk_score", 50)
        gemini_score = gemini_result.get("risk_score", 50)

        # Calculate deviation
        score_deviation = abs(openai_score - gemini_score)
        score_deviation_percent = (score_deviation / 100) * 100

        # Extract confidence scores
        openai_confidence = openai_result.get("confidence", 0.5)
        gemini_confidence = gemini_result.get("confidence", 0.5)

        confidence_delta = abs(openai_confidence - gemini_confidence)

        # Determine agreement
        high_deviation = score_deviation > self.deviation_threshold
        agreement = not high_deviation

        # Calculate average scores
        avg_score = (openai_score + gemini_score) / 2
        avg_confidence = (openai_confidence + gemini_confidence) / 2

        return {
            "openai_score": openai_score,
            "gemini_score": gemini_score,
            "score_deviation": score_deviation,
            "score_deviation_percent": score_deviation_percent,
            "openai_confidence": openai_confidence,
            "gemini_confidence": gemini_confidence,
            "confidence_delta": confidence_delta,
            "agreement": agreement,
            "high_deviation": high_deviation,
            "avg_score": avg_score,
            "avg_confidence": avg_confidence,
            "deviation_threshold": self.deviation_threshold
        }

    def _make_decision(
        self,
        openai_result: Dict[str, Any],
        gemini_result: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make final ensemble decision based on both analyses.

        Args:
            openai_result: OpenAI analysis result
            gemini_result: Gemini analysis result
            comparison: Comparison metrics

        Returns:
            Dictionary with ensemble decision and reasoning
        """
        if comparison["high_deviation"]:
            # High deviation - escalate to human review
            decision_type = "ESCALATE"
            reasoning = (
                f"High deviation detected ({comparison['score_deviation']:.0f} points). "
                f"OpenAI: {comparison['openai_score']}, Gemini: {comparison['gemini_score']}. "
                f"Recommend human review for final decision."
            )
            final_score = comparison["avg_score"]
            confidence = min(comparison["openai_confidence"], comparison["gemini_confidence"])

        elif comparison["agreement"]:
            # Models agree - accept consensus
            decision_type = "CONSENSUS"

            # Prefer the model with higher confidence
            if comparison["openai_confidence"] > comparison["gemini_confidence"]:
                final_score = comparison["openai_score"]
                confidence = comparison["openai_confidence"]
                preferred_model = "OpenAI"
            else:
                final_score = comparison["gemini_score"]
                confidence = comparison["gemini_confidence"]
                preferred_model = "Gemini"

            reasoning = (
                f"Models in agreement (deviation: {comparison['score_deviation']:.0f} points). "
                f"Using {preferred_model} result with higher confidence ({confidence:.2f})."
            )

        else:
            # Moderate deviation - use weighted average
            decision_type = "WEIGHTED_AVERAGE"

            # Weight by confidence
            total_confidence = comparison["openai_confidence"] + comparison["gemini_confidence"]
            if total_confidence > 0:
                openai_weight = comparison["openai_confidence"] / total_confidence
                gemini_weight = comparison["gemini_confidence"] / total_confidence

                final_score = (
                    comparison["openai_score"] * openai_weight +
                    comparison["gemini_score"] * gemini_weight
                )
            else:
                final_score = comparison["avg_score"]

            confidence = comparison["avg_confidence"]

            reasoning = (
                f"Moderate deviation ({comparison['score_deviation']:.0f} points). "
                f"Using confidence-weighted average: {final_score:.0f}."
            )

        # Determine risk level
        if final_score >= 80:
            risk_level = "CRITICAL"
        elif final_score >= 60:
            risk_level = "HIGH"
        elif final_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "decision_type": decision_type,
            "final_score": round(final_score, 1),
            "risk_level": risk_level,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "requires_human_review": comparison["high_deviation"],
            "model_agreement": comparison["agreement"]
        }

    def _update_metrics(
        self,
        openai_result: Dict[str, Any],
        gemini_result: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> None:
        """Update ensemble metrics."""
        self.metrics["total_requests"] += 1

        if comparison["agreement"]:
            self.metrics["agreements"] += 1
        else:
            self.metrics["disagreements"] += 1

        if comparison["high_deviation"]:
            self.metrics["escalations"] += 1

        # Aggregate costs
        openai_cost = openai_result.get("metadata", {}).get("cost", 0)
        gemini_cost = gemini_result.get("metadata", {}).get("cost", 0)
        self.metrics["total_cost"] += (openai_cost + gemini_cost)

        # Track max latency (parallel execution)
        openai_latency = openai_result.get("metadata", {}).get("latency", 0)
        gemini_latency = gemini_result.get("metadata", {}).get("latency", 0)
        self.metrics["total_latency"] += max(openai_latency, gemini_latency)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get ensemble service metrics.

        Returns:
            Dictionary with accumulated metrics
        """
        if self.metrics["total_requests"] > 0:
            agreement_rate = self.metrics["agreements"] / self.metrics["total_requests"]
            escalation_rate = self.metrics["escalations"] / self.metrics["total_requests"]
            avg_latency = self.metrics["total_latency"] / self.metrics["total_requests"]
        else:
            agreement_rate = 0.0
            escalation_rate = 0.0
            avg_latency = 0.0

        return {
            **self.metrics,
            "agreement_rate": agreement_rate,
            "escalation_rate": escalation_rate,
            "avg_latency": avg_latency
        }

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self.metrics = {
            "total_requests": 0,
            "agreements": 0,
            "disagreements": 0,
            "escalations": 0,
            "total_cost": 0.0,
            "total_latency": 0.0
        }
