"""
OpenAI Service - Risk Scoring and Compliance Analysis
Uses AI Gateway for structured outputs and risk assessment
"""

import json
from typing import Dict, Any, Optional
from app.models.task import Task
from app.gateway import AIGateway


class OpenAIService:
    """
    OpenAI service for risk scoring and compliance analysis.

    Features:
    - Structured JSON outputs for risk scores
    - Compliance explanation generation
    - Fraud detection analysis
    - Metrics tracking (tokens, cost, latency)
    """

    def __init__(self, gateway: Optional[AIGateway] = None):
        """
        Initialize OpenAI service.

        Args:
            gateway: AI Gateway instance (creates new if not provided)
        """
        self.gateway = gateway or AIGateway()
        self.metrics = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_latency": 0.0,
            "avg_confidence": 0.0
        }

    def analyze_risk(self, task: Task, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Analyze task for risk indicators with structured JSON output.

        Args:
            task: Task object to analyze
            temperature: Sampling temperature (lower for more deterministic)

        Returns:
            Dictionary with risk score, confidence, reasoning, and metadata
        """
        # Construct risk analysis prompt
        messages = [
            {
                "role": "system",
                "content": """You are an expert risk analyst for financial services.
Analyze the given scenario and provide a structured risk assessment.

Return your response in JSON format with these exact fields:
{
  "risk_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "risk_level": <string: "LOW", "MEDIUM", "HIGH", "CRITICAL">,
  "primary_concerns": [<list of main risk factors>],
  "recommendation": <string: recommended action>,
  "reasoning": <string: detailed explanation>
}"""
            },
            {
                "role": "user",
                "content": f"""Task Type: {task.task_type}
Business Impact: {task.business_impact}

Scenario:
{task.description}

Provide comprehensive risk analysis."""
            }
        ]

        # Call OpenAI via gateway with JSON mode
        response = self.gateway.call_openai(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=1000
        )

        # Update metrics
        self._update_metrics(response)

        # Parse and validate response
        if response["success"]:
            try:
                risk_data = json.loads(response["content"])

                return {
                    "risk_score": risk_data.get("risk_score", 50),
                    "confidence": risk_data.get("confidence", 0.5),
                    "risk_level": risk_data.get("risk_level", "MEDIUM"),
                    "primary_concerns": risk_data.get("primary_concerns", []),
                    "recommendation": risk_data.get("recommendation", "Review required"),
                    "reasoning": risk_data.get("reasoning", "No reasoning provided"),
                    "metadata": {
                        "provider": "openai",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                return self._error_result(f"Invalid JSON response: {response['content']}")
        else:
            return self._error_result(response["error"])

    def get_compliance_explanation(
        self,
        task: Task,
        regulation: str = "General FinTech Compliance",
        temperature: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate compliance analysis and explanation.

        Args:
            task: Task object to analyze
            regulation: Specific regulation to check against
            temperature: Sampling temperature

        Returns:
            Dictionary with compliance assessment and explanation
        """
        messages = [
            {
                "role": "system",
                "content": f"""You are a compliance expert specializing in {regulation}.
Analyze the scenario for compliance implications and provide structured guidance.

Return JSON format:
{{
  "compliant": <boolean>,
  "confidence": <float 0.0-1.0>,
  "violations": [<list of potential violations>],
  "requirements": [<list of applicable requirements>],
  "recommendations": [<list of actions to ensure compliance>],
  "explanation": <string: detailed analysis>
}}"""
            },
            {
                "role": "user",
                "content": f"""Regulation: {regulation}
Task: {task.task_type}

Scenario:
{task.description}

Provide compliance analysis."""
            }
        ]

        response = self.gateway.call_openai(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=1500
        )

        self._update_metrics(response)

        if response["success"]:
            try:
                compliance_data = json.loads(response["content"])

                return {
                    "compliant": compliance_data.get("compliant", None),
                    "confidence": compliance_data.get("confidence", 0.5),
                    "violations": compliance_data.get("violations", []),
                    "requirements": compliance_data.get("requirements", []),
                    "recommendations": compliance_data.get("recommendations", []),
                    "explanation": compliance_data.get("explanation", ""),
                    "metadata": {
                        "provider": "openai",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                return self._error_result(f"Invalid JSON response: {response['content']}")
        else:
            return self._error_result(response["error"])

    def detect_fraud_patterns(self, task: Task, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Detect fraud patterns in transaction or behavior data.

        Args:
            task: Task object with transaction/behavior details
            temperature: Sampling temperature (very low for fraud detection)

        Returns:
            Dictionary with fraud detection results
        """
        messages = [
            {
                "role": "system",
                "content": """You are a fraud detection expert for digital payments and lending.
Analyze the scenario for fraud indicators and suspicious patterns.

Return JSON format:
{
  "fraud_probability": <float 0.0-1.0>,
  "fraud_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "detected_patterns": [<list of fraud patterns found>],
  "red_flags": [<list of suspicious indicators>],
  "recommended_action": <string: APPROVE, REVIEW, REJECT, ESCALATE>,
  "explanation": <string: detailed reasoning>
}"""
            },
            {
                "role": "user",
                "content": f"""Transaction/Behavior Analysis:

{task.description}

Detect fraud patterns and assess risk."""
            }
        ]

        response = self.gateway.call_openai(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=1200
        )

        self._update_metrics(response)

        if response["success"]:
            try:
                fraud_data = json.loads(response["content"])

                return {
                    "fraud_probability": fraud_data.get("fraud_probability", 0.5),
                    "fraud_score": fraud_data.get("fraud_score", 50),
                    "confidence": fraud_data.get("confidence", 0.5),
                    "detected_patterns": fraud_data.get("detected_patterns", []),
                    "red_flags": fraud_data.get("red_flags", []),
                    "recommended_action": fraud_data.get("recommended_action", "REVIEW"),
                    "explanation": fraud_data.get("explanation", ""),
                    "metadata": {
                        "provider": "openai",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                return self._error_result(f"Invalid JSON response: {response['content']}")
        else:
            return self._error_result(response["error"])

    def _update_metrics(self, response: Dict[str, Any]) -> None:
        """Update service metrics with response data."""
        if response["success"]:
            self.metrics["total_requests"] += 1
            self.metrics["total_input_tokens"] += response["input_tokens"]
            self.metrics["total_output_tokens"] += response["output_tokens"]
            self.metrics["total_cost"] += response["cost"]
            self.metrics["total_latency"] += response["latency"]

    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "risk_score": 50,
            "confidence": 0.0,
            "risk_level": "UNKNOWN",
            "primary_concerns": [],
            "recommendation": "Manual review required",
            "reasoning": f"Error: {error_message}",
            "metadata": {
                "provider": "openai",
                "error": error_message
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Dictionary with accumulated metrics
        """
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0
            else 0.0
        )

        return {
            **self.metrics,
            "avg_latency": avg_latency,
            "total_tokens": self.metrics["total_input_tokens"] + self.metrics["total_output_tokens"]
        }

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self.metrics = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_latency": 0.0,
            "avg_confidence": 0.0
        }
