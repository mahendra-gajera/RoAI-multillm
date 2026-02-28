"""
RoAI Calculator - Return on AI Investment
Calculates business value and ROI from LLM deployment
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class RoAICalculator:
    """
    Calculator for Return on AI (RoAI) metrics.

    Formula: RoAI = (Value Generated - LLM Cost) / LLM Cost

    Value Generated = Fraud Prevented + Manual Cost Saved + Efficiency Gains
    """

    def __init__(self):
        """Initialize RoAI calculator with configuration."""
        # Default values from environment
        self.manual_review_cost_per_hour = float(
            os.getenv("MANUAL_REVIEW_COST_PER_HOUR", "100")
        )
        self.avg_fraud_prevention_value = float(
            os.getenv("AVERAGE_FRAUD_PREVENTION_VALUE", "5000")
        )

        # Session tracking
        self.session_metrics = {
            "start_time": datetime.now(),
            "total_llm_cost": 0.0,
            "fraud_prevented": 0.0,
            "manual_hours_saved": 0.0,
            "false_positives_avoided": 0,
            "requests_processed": 0
        }

    def calculate_roai(
        self,
        fraud_prevented: float,
        manual_cost_saved: float,
        llm_cost: float,
        additional_value: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculate Return on AI investment.

        Args:
            fraud_prevented: Dollar value of fraud caught/prevented
            manual_cost_saved: Cost saved from automation (hours × rate)
            llm_cost: Total LLM API costs
            additional_value: Any additional business value generated

        Returns:
            Dictionary with RoAI metrics and breakdown
        """
        # Calculate total value generated
        total_value = fraud_prevented + manual_cost_saved + additional_value

        # Calculate RoAI
        if llm_cost > 0:
            roai = (total_value - llm_cost) / llm_cost
            net_value = total_value - llm_cost
        else:
            roai = 0.0
            net_value = total_value

        # Calculate cost efficiency
        cost_per_dollar_value = llm_cost / total_value if total_value > 0 else 0.0

        return {
            "roai": round(roai, 2),
            "roai_multiplier": f"{roai:.1f}x",
            "total_value_generated": round(total_value, 2),
            "llm_cost": round(llm_cost, 4),
            "net_value": round(net_value, 2),
            "cost_per_dollar_value": round(cost_per_dollar_value, 4),
            "breakdown": {
                "fraud_prevented": round(fraud_prevented, 2),
                "manual_cost_saved": round(manual_cost_saved, 2),
                "additional_value": round(additional_value, 2)
            },
            "roi_percent": round(roai * 100, 1)
        }

    def calculate_manual_cost_saved(
        self,
        tasks_automated: int,
        minutes_per_task: float,
        hourly_rate: Optional[float] = None
    ) -> float:
        """
        Calculate cost saved from task automation.

        Args:
            tasks_automated: Number of tasks automated
            minutes_per_task: Average minutes per manual task
            hourly_rate: Hourly cost for manual review (uses default if None)

        Returns:
            Total cost saved in dollars
        """
        rate = hourly_rate or self.manual_review_cost_per_hour
        hours_saved = (tasks_automated * minutes_per_task) / 60
        cost_saved = hours_saved * rate

        return round(cost_saved, 2)

    def estimate_fraud_value(
        self,
        high_risk_alerts: int,
        detection_accuracy: float = 0.85,
        avg_fraud_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Estimate value from fraud prevention.

        Args:
            high_risk_alerts: Number of high-risk alerts flagged
            detection_accuracy: Estimated accuracy rate (0-1)
            avg_fraud_value: Average fraud value per case

        Returns:
            Dictionary with fraud prevention value estimate
        """
        avg_value = avg_fraud_value or self.avg_fraud_prevention_value

        # Estimate actual fraud caught
        estimated_fraud_caught = int(high_risk_alerts * detection_accuracy)
        total_fraud_value = estimated_fraud_caught * avg_value

        # Calculate precision metrics
        false_positives = high_risk_alerts - estimated_fraud_caught

        return {
            "total_fraud_value": round(total_fraud_value, 2),
            "estimated_fraud_cases": estimated_fraud_caught,
            "high_risk_alerts": high_risk_alerts,
            "detection_accuracy": detection_accuracy,
            "avg_fraud_value": avg_value,
            "false_positives": false_positives,
            "precision": round(detection_accuracy, 2)
        }

    def track_session_value(
        self,
        llm_cost: float = 0.0,
        fraud_prevented: float = 0.0,
        manual_hours_saved: float = 0.0,
        requests: int = 1
    ) -> None:
        """
        Track value generated in current session.

        Args:
            llm_cost: LLM cost to add
            fraud_prevented: Fraud value prevented
            manual_hours_saved: Hours of manual work saved
            requests: Number of requests processed
        """
        self.session_metrics["total_llm_cost"] += llm_cost
        self.session_metrics["fraud_prevented"] += fraud_prevented
        self.session_metrics["manual_hours_saved"] += manual_hours_saved
        self.session_metrics["requests_processed"] += requests

    def get_session_roai(self) -> Dict[str, Any]:
        """
        Calculate RoAI for current session.

        Returns:
            Dictionary with session RoAI metrics
        """
        # Calculate manual cost saved
        manual_cost_saved = (
            self.session_metrics["manual_hours_saved"] *
            self.manual_review_cost_per_hour
        )

        # Calculate session duration
        duration = (datetime.now() - self.session_metrics["start_time"]).total_seconds()

        # Calculate RoAI
        roai_result = self.calculate_roai(
            fraud_prevented=self.session_metrics["fraud_prevented"],
            manual_cost_saved=manual_cost_saved,
            llm_cost=self.session_metrics["total_llm_cost"]
        )

        # Add session-specific metrics
        roai_result["session"] = {
            "duration_seconds": round(duration, 1),
            "duration_minutes": round(duration / 60, 1),
            "requests_processed": self.session_metrics["requests_processed"],
            "avg_cost_per_request": round(
                self.session_metrics["total_llm_cost"] / self.session_metrics["requests_processed"]
                if self.session_metrics["requests_processed"] > 0 else 0.0,
                6
            ),
            "manual_hours_saved": round(self.session_metrics["manual_hours_saved"], 2)
        }

        return roai_result

    def compare_scenarios(
        self,
        scenario_a: Dict[str, float],
        scenario_b: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Compare RoAI between two scenarios (e.g., with vs without intelligent routing).

        Args:
            scenario_a: First scenario metrics (fraud_prevented, manual_cost_saved, llm_cost)
            scenario_b: Second scenario metrics

        Returns:
            Dictionary with comparison analysis
        """
        roai_a = self.calculate_roai(
            fraud_prevented=scenario_a.get("fraud_prevented", 0),
            manual_cost_saved=scenario_a.get("manual_cost_saved", 0),
            llm_cost=scenario_a.get("llm_cost", 0)
        )

        roai_b = self.calculate_roai(
            fraud_prevented=scenario_b.get("fraud_prevented", 0),
            manual_cost_saved=scenario_b.get("manual_cost_saved", 0),
            llm_cost=scenario_b.get("llm_cost", 0)
        )

        roai_improvement = roai_b["roai"] - roai_a["roai"]
        cost_reduction = scenario_a.get("llm_cost", 0) - scenario_b.get("llm_cost", 0)
        net_value_improvement = roai_b["net_value"] - roai_a["net_value"]

        return {
            "scenario_a": roai_a,
            "scenario_b": roai_b,
            "improvement": {
                "roai_delta": round(roai_improvement, 2),
                "cost_reduction": round(cost_reduction, 4),
                "net_value_improvement": round(net_value_improvement, 2),
                "percent_improvement": round(
                    (roai_improvement / roai_a["roai"] * 100) if roai_a["roai"] != 0 else 0,
                    1
                )
            },
            "winner": "scenario_b" if roai_b["roai"] > roai_a["roai"] else "scenario_a"
        }

    def project_annual_value(
        self,
        daily_requests: int,
        current_roai: float,
        avg_cost_per_request: float
    ) -> Dict[str, Any]:
        """
        Project annual value based on current metrics.

        Args:
            daily_requests: Average daily requests
            current_roai: Current RoAI multiplier
            avg_cost_per_request: Average cost per request

        Returns:
            Dictionary with annual projections
        """
        # Calculate annual volumes
        annual_requests = daily_requests * 365
        annual_llm_cost = annual_requests * avg_cost_per_request

        # Project value based on RoAI
        annual_value_generated = annual_llm_cost * (1 + current_roai)
        annual_net_value = annual_llm_cost * current_roai

        return {
            "annual_requests": annual_requests,
            "annual_llm_cost": round(annual_llm_cost, 2),
            "annual_value_generated": round(annual_value_generated, 2),
            "annual_net_value": round(annual_net_value, 2),
            "roai_multiplier": f"{current_roai:.1f}x",
            "assumptions": {
                "daily_requests": daily_requests,
                "avg_cost_per_request": round(avg_cost_per_request, 6),
                "current_roai": current_roai
            }
        }

    def calculate_payback_period(
        self,
        implementation_cost: float,
        monthly_net_value: float
    ) -> Dict[str, Any]:
        """
        Calculate payback period for LLM implementation.

        Args:
            implementation_cost: One-time setup/implementation cost
            monthly_net_value: Monthly net value generated

        Returns:
            Dictionary with payback analysis
        """
        if monthly_net_value <= 0:
            return {
                "payback_months": float('inf'),
                "payback_message": "No positive net value - payback not achievable",
                "breakeven": False
            }

        payback_months = implementation_cost / monthly_net_value

        return {
            "payback_months": round(payback_months, 1),
            "payback_days": round(payback_months * 30, 0),
            "implementation_cost": round(implementation_cost, 2),
            "monthly_net_value": round(monthly_net_value, 2),
            "breakeven": True,
            "payback_message": f"Payback achieved in {payback_months:.1f} months"
        }

    def reset_session(self) -> None:
        """Reset session metrics."""
        self.session_metrics = {
            "start_time": datetime.now(),
            "total_llm_cost": 0.0,
            "fraud_prevented": 0.0,
            "manual_hours_saved": 0.0,
            "false_positives_avoided": 0,
            "requests_processed": 0
        }

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Dictionary with RoAI calculation parameters
        """
        return {
            "manual_review_cost_per_hour": self.manual_review_cost_per_hour,
            "avg_fraud_prevention_value": self.avg_fraud_prevention_value,
            "formula": "RoAI = (Fraud Prevented + Manual Cost Saved - LLM Cost) / LLM Cost"
        }
