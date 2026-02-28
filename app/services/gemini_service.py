"""
Gemini Service - Long-Context and Multi-Document Analysis
Uses AI Gateway for extended context processing and correlation
"""

import json
from typing import Dict, Any, List, Optional
from app.models.task import Task
from app.gateway import AIGateway


class GeminiService:
    """
    Gemini service for long-context analysis and multi-document processing.

    Features:
    - Long-context analysis (100k+ tokens)
    - Multi-document correlation
    - Cross-reference fraud investigation
    - Metrics tracking (tokens, cost, latency)
    """

    def __init__(self, gateway: Optional[AIGateway] = None):
        """
        Initialize Gemini service.

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

    def analyze_long_context(self, task: Task, temperature: float = 0.5) -> Dict[str, Any]:
        """
        Analyze task with large context (>80k tokens).

        Args:
            task: Task object with large context
            temperature: Sampling temperature

        Returns:
            Dictionary with analysis results and metadata
        """
        messages = [
            {
                "role": "user",
                "content": f"""You are an expert analyst for financial risk assessment.
Analyze the following extensive scenario and provide comprehensive insights.

Task Type: {task.task_type}
Context Length: {task.context_length:,} tokens
Business Impact: {task.business_impact}

Scenario:
{task.description}

Provide a detailed analysis in JSON format with these fields:
{{
  "risk_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "summary": <string: executive summary>,
  "key_findings": [<list of important findings>],
  "correlations": [<list of identified patterns/correlations>],
  "recommendations": [<list of recommended actions>],
  "detailed_analysis": <string: comprehensive analysis>
}}"""
            }
        ]

        response = self.gateway.call_gemini(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )

        self._update_metrics(response)

        if response["success"]:
            try:
                # Try to parse as JSON
                content = response["content"].strip()

                # Handle markdown code blocks
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                analysis_data = json.loads(content)

                return {
                    "risk_score": analysis_data.get("risk_score", 50),
                    "confidence": analysis_data.get("confidence", 0.7),
                    "summary": analysis_data.get("summary", ""),
                    "key_findings": analysis_data.get("key_findings", []),
                    "correlations": analysis_data.get("correlations", []),
                    "recommendations": analysis_data.get("recommendations", []),
                    "detailed_analysis": analysis_data.get("detailed_analysis", ""),
                    "metadata": {
                        "provider": "gemini",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                # Fallback to text response if JSON parsing fails
                return self._text_fallback_result(response)
        else:
            return self._error_result(response["error"])

    def multi_document_correlation(
        self,
        task: Task,
        documents: Optional[List[str]] = None,
        temperature: float = 0.4
    ) -> Dict[str, Any]:
        """
        Analyze multiple documents for correlation and fraud patterns.

        Args:
            task: Task object describing the analysis
            documents: List of document contents (optional, can be in task.description)
            temperature: Sampling temperature

        Returns:
            Dictionary with correlation analysis and findings
        """
        # Prepare document context
        if documents:
            doc_context = "\n\n".join([
                f"--- Document {i+1} ---\n{doc}"
                for i, doc in enumerate(documents)
            ])
        else:
            doc_context = task.description

        messages = [
            {
                "role": "user",
                "content": f"""You are an expert fraud investigator analyzing multiple documents.
Cross-reference the documents below to identify patterns, correlations, and anomalies.

Task Type: {task.task_type}
Number of Documents: {len(documents) if documents else 'Multiple'}
Business Impact: {task.business_impact}

Documents:
{doc_context}

Provide correlation analysis in JSON format:
{{
  "correlation_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "suspicious_patterns": [<list of suspicious patterns found>],
  "document_links": [<list of connections between documents>],
  "anomalies": [<list of detected anomalies>],
  "risk_assessment": <string: overall risk assessment>,
  "recommended_action": <string: APPROVE, INVESTIGATE, ESCALATE, REJECT>,
  "detailed_findings": <string: comprehensive findings>
}}"""
            }
        ]

        response = self.gateway.call_gemini(
            messages=messages,
            temperature=temperature,
            max_tokens=2500
        )

        self._update_metrics(response)

        if response["success"]:
            try:
                content = response["content"].strip()

                # Handle markdown code blocks
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                correlation_data = json.loads(content)

                return {
                    "correlation_score": correlation_data.get("correlation_score", 50),
                    "confidence": correlation_data.get("confidence", 0.7),
                    "suspicious_patterns": correlation_data.get("suspicious_patterns", []),
                    "document_links": correlation_data.get("document_links", []),
                    "anomalies": correlation_data.get("anomalies", []),
                    "risk_assessment": correlation_data.get("risk_assessment", ""),
                    "recommended_action": correlation_data.get("recommended_action", "INVESTIGATE"),
                    "detailed_findings": correlation_data.get("detailed_findings", ""),
                    "metadata": {
                        "provider": "gemini",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                return self._text_fallback_result(response)
        else:
            return self._error_result(response["error"])

    def analyze_document_risk(
        self,
        task: Task,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        General document risk analysis (contracts, loan applications, etc.).

        Args:
            task: Task object with document content
            temperature: Sampling temperature

        Returns:
            Dictionary with document risk analysis
        """
        messages = [
            {
                "role": "user",
                "content": f"""Analyze the following document for risk indicators and compliance issues.

Task Type: {task.task_type}
Document:
{task.description}

Provide analysis in JSON format:
{{
  "risk_score": <integer 0-100>,
  "confidence": <float 0.0-1.0>,
  "risk_factors": [<list of identified risk factors>],
  "compliance_concerns": [<list of compliance issues>],
  "missing_information": [<list of missing or incomplete information>],
  "recommendation": <string: recommended decision>,
  "explanation": <string: detailed explanation>
}}"""
            }
        ]

        response = self.gateway.call_gemini(
            messages=messages,
            temperature=temperature,
            max_tokens=1500
        )

        self._update_metrics(response)

        if response["success"]:
            try:
                content = response["content"].strip()

                # Handle markdown code blocks
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()

                doc_data = json.loads(content)

                return {
                    "risk_score": doc_data.get("risk_score", 50),
                    "confidence": doc_data.get("confidence", 0.7),
                    "risk_factors": doc_data.get("risk_factors", []),
                    "compliance_concerns": doc_data.get("compliance_concerns", []),
                    "missing_information": doc_data.get("missing_information", []),
                    "recommendation": doc_data.get("recommendation", "Review required"),
                    "explanation": doc_data.get("explanation", ""),
                    "metadata": {
                        "provider": "gemini",
                        "model": response["model"],
                        "input_tokens": response["input_tokens"],
                        "output_tokens": response["output_tokens"],
                        "cost": response["cost"],
                        "latency": response["latency"]
                    }
                }
            except json.JSONDecodeError:
                return self._text_fallback_result(response)
        else:
            return self._error_result(response["error"])

    def _text_fallback_result(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create result from text response when JSON parsing fails.

        Args:
            response: Gateway response

        Returns:
            Standardized result dictionary
        """
        return {
            "risk_score": 50,
            "confidence": 0.6,
            "summary": response["content"][:500],
            "key_findings": [],
            "recommendations": ["Manual review recommended due to parsing issues"],
            "detailed_analysis": response["content"],
            "metadata": {
                "provider": "gemini",
                "model": response["model"],
                "input_tokens": response["input_tokens"],
                "output_tokens": response["output_tokens"],
                "cost": response["cost"],
                "latency": response["latency"],
                "note": "JSON parsing failed, returning text response"
            }
        }

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
            "summary": "Error occurred during analysis",
            "key_findings": [],
            "recommendations": ["Manual review required due to error"],
            "detailed_analysis": f"Error: {error_message}",
            "metadata": {
                "provider": "gemini",
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
