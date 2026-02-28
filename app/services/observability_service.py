"""
Observability Service - Metrics Tracking and Dashboard Data
Aggregates metrics from all LLM services for monitoring and analysis
"""

from typing import Dict, Any, List
from datetime import datetime
import json


class ObservabilityService:
    """
    Central observability service for tracking all LLM interactions.

    Features:
    - Per-model metrics aggregation
    - Session-level statistics
    - Cost tracking and analysis
    - Performance monitoring
    - RoAI calculation support
    """

    def __init__(self):
        """Initialize observability service with empty metrics."""
        self.session_start = datetime.now()
        self.requests = []  # Store individual request details

        # Aggregate metrics by provider
        self.metrics = {
            "openai": {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "total_latency": 0.0,
                "successful_requests": 0,
                "failed_requests": 0
            },
            "gemini": {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "total_latency": 0.0,
                "successful_requests": 0,
                "failed_requests": 0
            },
            "ensemble": {
                "total_requests": 0,
                "agreements": 0,
                "disagreements": 0,
                "escalations": 0,
                "total_cost": 0.0,
                "total_latency": 0.0
            }
        }

    def log_request(
        self,
        provider: str,
        task_type: str,
        metadata: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Log individual request with full details.

        Args:
            provider: Provider name (openai, gemini, ensemble)
            task_type: Type of task performed
            metadata: Request metadata (tokens, cost, latency, etc.)
            result: Analysis result
        """
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "task_type": task_type,
            "metadata": metadata,
            "success": metadata.get("error") is None,
            "risk_score": result.get("risk_score") or result.get("final_score"),
            "confidence": result.get("confidence", 0.0)
        }

        self.requests.append(request_record)

        # Update aggregate metrics
        self._update_aggregate_metrics(provider, metadata, request_record["success"])

    def _update_aggregate_metrics(
        self,
        provider: str,
        metadata: Dict[str, Any],
        success: bool
    ) -> None:
        """
        Update aggregate metrics for a provider.

        Args:
            provider: Provider name
            metadata: Request metadata
            success: Whether request was successful
        """
        if provider not in self.metrics:
            return

        metrics = self.metrics[provider]
        metrics["total_requests"] += 1

        if success:
            metrics["successful_requests"] = metrics.get("successful_requests", 0) + 1
        else:
            metrics["failed_requests"] = metrics.get("failed_requests", 0) + 1

        # Update token counts
        if "input_tokens" in metadata:
            metrics["total_input_tokens"] += metadata["input_tokens"]
        if "output_tokens" in metadata:
            metrics["total_output_tokens"] += metadata["output_tokens"]

        # Update cost and latency
        if "cost" in metadata:
            metrics["total_cost"] += metadata["cost"]
        if "latency" in metadata:
            metrics["total_latency"] += metadata["latency"]

    def log_ensemble_request(
        self,
        ensemble_result: Dict[str, Any]
    ) -> None:
        """
        Log ensemble request with comparison data.

        Args:
            ensemble_result: Complete ensemble analysis result
        """
        comparison = ensemble_result.get("comparison", {})
        decision = ensemble_result.get("ensemble_decision", {})
        metadata = ensemble_result.get("metadata", {})

        request_record = {
            "timestamp": datetime.now().isoformat(),
            "provider": "ensemble",
            "task_type": "ensemble_validation",
            "metadata": metadata,
            "success": True,
            "risk_score": decision.get("final_score"),
            "confidence": decision.get("confidence", 0.0),
            "agreement": comparison.get("agreement", False),
            "deviation": comparison.get("score_deviation", 0)
        }

        self.requests.append(request_record)

        # Update ensemble-specific metrics
        ensemble_metrics = self.metrics["ensemble"]
        ensemble_metrics["total_requests"] += 1

        if comparison.get("agreement", False):
            ensemble_metrics["agreements"] += 1
        else:
            ensemble_metrics["disagreements"] += 1

        if comparison.get("high_deviation", False):
            ensemble_metrics["escalations"] += 1

        if "cost" in metadata:
            ensemble_metrics["total_cost"] += metadata["cost"]
        if "latency" in metadata:
            ensemble_metrics["total_latency"] += metadata["latency"]

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics for dashboard display.

        Returns:
            Dictionary with formatted metrics for UI
        """
        # Calculate totals across all providers
        total_requests = sum(
            self.metrics[p].get("total_requests", 0)
            for p in ["openai", "gemini", "ensemble"]
        )

        total_cost = sum(
            self.metrics[p].get("total_cost", 0.0)
            for p in ["openai", "gemini", "ensemble"]
        )

        # Calculate distribution percentages
        if total_requests > 0:
            openai_pct = (self.metrics["openai"]["total_requests"] / total_requests) * 100
            gemini_pct = (self.metrics["gemini"]["total_requests"] / total_requests) * 100
            ensemble_pct = (self.metrics["ensemble"]["total_requests"] / total_requests) * 100
        else:
            openai_pct = gemini_pct = ensemble_pct = 0.0

        # Calculate average latencies
        openai_avg_latency = self._calculate_avg_latency("openai")
        gemini_avg_latency = self._calculate_avg_latency("gemini")
        ensemble_avg_latency = self._calculate_avg_latency("ensemble")

        # Get ensemble-specific metrics
        ensemble_metrics = self.metrics["ensemble"]
        agreement_rate = (
            (ensemble_metrics["agreements"] / ensemble_metrics["total_requests"] * 100)
            if ensemble_metrics["total_requests"] > 0 else 0.0
        )
        escalation_rate = (
            (ensemble_metrics["escalations"] / ensemble_metrics["total_requests"] * 100)
            if ensemble_metrics["total_requests"] > 0 else 0.0
        )

        return {
            "session": {
                "start_time": self.session_start.isoformat(),
                "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
                "total_requests": total_requests,
                "total_cost": round(total_cost, 4)
            },
            "distribution": {
                "openai": {
                    "count": self.metrics["openai"]["total_requests"],
                    "percentage": round(openai_pct, 1)
                },
                "gemini": {
                    "count": self.metrics["gemini"]["total_requests"],
                    "percentage": round(gemini_pct, 1)
                },
                "ensemble": {
                    "count": self.metrics["ensemble"]["total_requests"],
                    "percentage": round(ensemble_pct, 1)
                }
            },
            "performance": {
                "openai": {
                    "avg_latency": round(openai_avg_latency, 3),
                    "total_cost": round(self.metrics["openai"]["total_cost"], 4),
                    "total_tokens": (
                        self.metrics["openai"]["total_input_tokens"] +
                        self.metrics["openai"]["total_output_tokens"]
                    )
                },
                "gemini": {
                    "avg_latency": round(gemini_avg_latency, 3),
                    "total_cost": round(self.metrics["gemini"]["total_cost"], 4),
                    "total_tokens": (
                        self.metrics["gemini"]["total_input_tokens"] +
                        self.metrics["gemini"]["total_output_tokens"]
                    )
                },
                "ensemble": {
                    "avg_latency": round(ensemble_avg_latency, 3),
                    "total_cost": round(self.metrics["ensemble"]["total_cost"], 4),
                    "agreement_rate": round(agreement_rate, 1),
                    "escalation_rate": round(escalation_rate, 1)
                }
            },
            "cost_breakdown": {
                "openai": round(self.metrics["openai"]["total_cost"], 4),
                "gemini": round(self.metrics["gemini"]["total_cost"], 4),
                "ensemble": round(self.metrics["ensemble"]["total_cost"], 4)
            }
        }

    def _calculate_avg_latency(self, provider: str) -> float:
        """Calculate average latency for a provider."""
        metrics = self.metrics.get(provider, {})
        total_requests = metrics.get("total_requests", 0)
        total_latency = metrics.get("total_latency", 0.0)

        return total_latency / total_requests if total_requests > 0 else 0.0

    def get_recent_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent requests.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of recent request records
        """
        return self.requests[-limit:]

    def get_cost_analysis(self) -> Dict[str, Any]:
        """
        Get detailed cost analysis.

        Returns:
            Dictionary with cost breakdown and insights
        """
        total_cost = sum(
            self.metrics[p].get("total_cost", 0.0)
            for p in ["openai", "gemini", "ensemble"]
        )

        # Calculate cost per request
        total_requests = sum(
            self.metrics[p].get("total_requests", 0)
            for p in ["openai", "gemini", "ensemble"]
        )

        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0

        # Find most expensive provider
        provider_costs = {
            "openai": self.metrics["openai"]["total_cost"],
            "gemini": self.metrics["gemini"]["total_cost"],
            "ensemble": self.metrics["ensemble"]["total_cost"]
        }

        most_expensive = max(provider_costs.items(), key=lambda x: x[1])[0] if total_cost > 0 else None

        return {
            "total_cost": round(total_cost, 4),
            "avg_cost_per_request": round(avg_cost_per_request, 4),
            "cost_by_provider": {
                k: round(v, 4) for k, v in provider_costs.items()
            },
            "most_expensive_provider": most_expensive
        }

    def export_metrics(self, filepath: str = None) -> str:
        """
        Export all metrics to JSON.

        Args:
            filepath: Optional file path to save metrics

        Returns:
            JSON string of metrics
        """
        export_data = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "export_time": datetime.now().isoformat()
            },
            "metrics": self.metrics,
            "requests": self.requests
        }

        json_data = json.dumps(export_data, indent=2)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_data)

        return json_data

    def reset_metrics(self) -> None:
        """Reset all metrics and start new session."""
        self.session_start = datetime.now()
        self.requests = []

        for provider in ["openai", "gemini", "ensemble"]:
            if provider == "ensemble":
                self.metrics[provider] = {
                    "total_requests": 0,
                    "agreements": 0,
                    "disagreements": 0,
                    "escalations": 0,
                    "total_cost": 0.0,
                    "total_latency": 0.0
                }
            else:
                self.metrics[provider] = {
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost": 0.0,
                    "total_latency": 0.0,
                    "successful_requests": 0,
                    "failed_requests": 0
                }
