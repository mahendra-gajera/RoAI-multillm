"""
Prompt Versioning and Management System
Supports A/B testing, version control, and prompt optimization
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib


class PromptVersion:
    """Single prompt version with metadata."""

    def __init__(
        self,
        prompt_id: str,
        version: str,
        template: str,
        variables: List[str],
        description: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.prompt_id = prompt_id
        self.version = version
        self.template = template
        self.variables = variables
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.performance_metrics = {
            "total_uses": 0,
            "avg_confidence": 0.0,
            "avg_latency": 0.0,
            "avg_cost": 0.0,
            "success_rate": 0.0
        }

    def render(self, **kwargs) -> str:
        """Render prompt with given variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt: {e}")

    def update_metrics(
        self,
        confidence: float,
        latency: float,
        cost: float,
        success: bool
    ):
        """Update performance metrics."""
        total = self.performance_metrics["total_uses"]

        # Running average
        self.performance_metrics["avg_confidence"] = (
            (self.performance_metrics["avg_confidence"] * total + confidence) / (total + 1)
        )
        self.performance_metrics["avg_latency"] = (
            (self.performance_metrics["avg_latency"] * total + latency) / (total + 1)
        )
        self.performance_metrics["avg_cost"] = (
            (self.performance_metrics["avg_cost"] * total + cost) / (total + 1)
        )

        # Success rate
        successes = self.performance_metrics["success_rate"] * total
        self.performance_metrics["success_rate"] = (
            (successes + (1 if success else 0)) / (total + 1)
        )

        self.performance_metrics["total_uses"] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template": self.template,
            "variables": self.variables,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "performance_metrics": self.performance_metrics
        }


class ABTestExperiment:
    """A/B testing experiment for prompts."""

    def __init__(
        self,
        experiment_id: str,
        name: str,
        variants: Dict[str, str],  # {variant_name: prompt_version}
        traffic_split: Dict[str, float] = None
    ):
        self.experiment_id = experiment_id
        self.name = name
        self.variants = variants
        self.traffic_split = traffic_split or {
            k: 1.0/len(variants) for k in variants.keys()
        }
        self.results = {
            variant: {
                "requests": 0,
                "avg_confidence": 0.0,
                "avg_latency": 0.0,
                "avg_cost": 0.0,
                "success_rate": 0.0
            }
            for variant in variants.keys()
        }
        self.created_at = datetime.now().isoformat()
        self.status = "running"  # running, paused, completed

    def select_variant(self, user_id: str = None) -> str:
        """Select variant based on traffic split."""
        import random

        # Use user_id for consistent assignment if provided
        if user_id:
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            rand_val = (hash_val % 100) / 100.0
        else:
            rand_val = random.random()

        cumulative = 0.0
        for variant, split in self.traffic_split.items():
            cumulative += split
            if rand_val < cumulative:
                return variant

        return list(self.variants.keys())[0]

    def record_result(
        self,
        variant: str,
        confidence: float,
        latency: float,
        cost: float,
        success: bool
    ):
        """Record experiment result."""
        if variant not in self.results:
            return

        result = self.results[variant]
        total = result["requests"]

        # Update running averages
        result["avg_confidence"] = (
            (result["avg_confidence"] * total + confidence) / (total + 1)
        )
        result["avg_latency"] = (
            (result["avg_latency"] * total + latency) / (total + 1)
        )
        result["avg_cost"] = (
            (result["avg_cost"] * total + cost) / (total + 1)
        )

        successes = result["success_rate"] * total
        result["success_rate"] = (successes + (1 if success else 0)) / (total + 1)

        result["requests"] += 1

    def get_winner(self, metric: str = "avg_confidence") -> Optional[str]:
        """Get winning variant based on metric."""
        if not any(r["requests"] > 0 for r in self.results.values()):
            return None

        return max(
            self.results.items(),
            key=lambda x: x[1].get(metric, 0)
        )[0]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "variants": self.variants,
            "traffic_split": self.traffic_split,
            "results": self.results,
            "created_at": self.created_at,
            "status": self.status
        }


class PromptManager:
    """
    Prompt versioning and A/B testing manager.

    Features:
    - Version control for prompts
    - A/B testing support
    - Performance tracking
    - Prompt templates library
    """

    def __init__(self, storage_path: str = "data/prompts"):
        """
        Initialize prompt manager.

        Args:
            storage_path: Directory to store prompt versions
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self.experiments: Dict[str, ABTestExperiment] = {}

        self._load_prompts()
        self._load_experiments()

    def create_prompt(
        self,
        prompt_id: str,
        template: str,
        variables: List[str],
        description: str = "",
        tags: List[str] = None,
        version: str = "v1.0"
    ) -> PromptVersion:
        """
        Create new prompt version.

        Args:
            prompt_id: Unique prompt identifier
            template: Prompt template with {variables}
            variables: List of required variables
            description: Human-readable description
            tags: Categorization tags
            version: Version string

        Returns:
            PromptVersion object
        """
        prompt = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            template=template,
            variables=variables,
            description=description,
            tags=tags
        )

        if prompt_id not in self.prompts:
            self.prompts[prompt_id] = {}

        self.prompts[prompt_id][version] = prompt
        self._save_prompt(prompt)

        return prompt

    def get_prompt(
        self,
        prompt_id: str,
        version: str = "latest"
    ) -> Optional[PromptVersion]:
        """
        Get prompt by ID and version.

        Args:
            prompt_id: Prompt identifier
            version: Version string or "latest"

        Returns:
            PromptVersion or None
        """
        if prompt_id not in self.prompts:
            return None

        if version == "latest":
            versions = sorted(
                self.prompts[prompt_id].keys(),
                reverse=True
            )
            version = versions[0] if versions else None

        return self.prompts[prompt_id].get(version)

    def create_experiment(
        self,
        name: str,
        prompt_id: str,
        variants: Dict[str, str],  # {variant_name: version}
        traffic_split: Dict[str, float] = None
    ) -> ABTestExperiment:
        """
        Create A/B testing experiment.

        Args:
            name: Experiment name
            prompt_id: Prompt ID to test
            variants: Variant names mapped to prompt versions
            traffic_split: Traffic allocation per variant

        Returns:
            ABTestExperiment object
        """
        experiment_id = f"{prompt_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )

        self.experiments[experiment_id] = experiment
        self._save_experiment(experiment)

        return experiment

    def get_prompt_for_experiment(
        self,
        experiment_id: str,
        user_id: str = None
    ) -> Optional[tuple[PromptVersion, str]]:
        """
        Get prompt variant for A/B test.

        Args:
            experiment_id: Experiment identifier
            user_id: Optional user ID for consistent assignment

        Returns:
            (PromptVersion, variant_name) or None
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != "running":
            return None

        variant_name = experiment.select_variant(user_id)
        version = experiment.variants[variant_name]

        # Extract prompt_id from experiment_id
        prompt_id = experiment_id.rsplit("_", 2)[0]
        prompt = self.get_prompt(prompt_id, version)

        return (prompt, variant_name) if prompt else None

    def record_prompt_performance(
        self,
        prompt_id: str,
        version: str,
        confidence: float,
        latency: float,
        cost: float,
        success: bool = True
    ):
        """Record prompt performance metrics."""
        prompt = self.get_prompt(prompt_id, version)
        if prompt:
            prompt.update_metrics(confidence, latency, cost, success)
            self._save_prompt(prompt)

    def record_experiment_result(
        self,
        experiment_id: str,
        variant: str,
        confidence: float,
        latency: float,
        cost: float,
        success: bool = True
    ):
        """Record A/B test result."""
        experiment = self.experiments.get(experiment_id)
        if experiment:
            experiment.record_result(variant, confidence, latency, cost, success)
            self._save_experiment(experiment)

    def get_prompt_analytics(self, prompt_id: str) -> Dict[str, Any]:
        """Get analytics for all versions of a prompt."""
        if prompt_id not in self.prompts:
            return {}

        return {
            version: prompt.performance_metrics
            for version, prompt in self.prompts[prompt_id].items()
        }

    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get A/B test results."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        winner = experiment.get_winner("avg_confidence")

        return {
            "experiment": experiment.to_dict(),
            "winner": winner,
            "statistical_significance": self._calculate_significance(experiment)
        }

    def _calculate_significance(self, experiment: ABTestExperiment) -> Dict[str, Any]:
        """Calculate statistical significance (simplified)."""
        # Simplified significance calculation
        # In production, use proper statistical tests
        variants = list(experiment.results.items())
        if len(variants) < 2:
            return {"significant": False, "confidence": 0.0}

        # Get two top variants
        sorted_variants = sorted(
            variants,
            key=lambda x: x[1]["avg_confidence"],
            reverse=True
        )

        if len(sorted_variants) < 2:
            return {"significant": False, "confidence": 0.0}

        best = sorted_variants[0][1]
        second = sorted_variants[1][1]

        diff = abs(best["avg_confidence"] - second["avg_confidence"])
        min_requests = min(best["requests"], second["requests"])

        # Simple heuristic: significant if >10% difference and >30 samples
        significant = diff > 0.1 and min_requests > 30

        return {
            "significant": significant,
            "confidence": min(diff * 10, 1.0),  # Rough confidence estimate
            "difference": diff,
            "sample_size": min_requests
        }

    def list_prompts(self, tags: List[str] = None) -> List[Dict[str, Any]]:
        """List all prompts, optionally filtered by tags."""
        results = []

        for prompt_id, versions in self.prompts.items():
            latest_version = sorted(versions.keys(), reverse=True)[0]
            prompt = versions[latest_version]

            if tags and not any(tag in prompt.tags for tag in tags):
                continue

            results.append({
                "prompt_id": prompt_id,
                "latest_version": latest_version,
                "total_versions": len(versions),
                "description": prompt.description,
                "tags": prompt.tags,
                "total_uses": prompt.performance_metrics["total_uses"]
            })

        return results

    def _save_prompt(self, prompt: PromptVersion):
        """Save prompt to disk."""
        file_path = self.storage_path / f"{prompt.prompt_id}_{prompt.version}.json"
        with open(file_path, 'w') as f:
            json.dump(prompt.to_dict(), f, indent=2)

    def _save_experiment(self, experiment: ABTestExperiment):
        """Save experiment to disk."""
        file_path = self.storage_path / f"experiment_{experiment.experiment_id}.json"
        with open(file_path, 'w') as f:
            json.dump(experiment.to_dict(), f, indent=2)

    def _load_prompts(self):
        """Load prompts from disk."""
        if not self.storage_path.exists():
            return

        for file_path in self.storage_path.glob("*.json"):
            if file_path.name.startswith("experiment_"):
                continue

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                prompt = PromptVersion(
                    prompt_id=data["prompt_id"],
                    version=data["version"],
                    template=data["template"],
                    variables=data["variables"],
                    description=data.get("description", ""),
                    tags=data.get("tags", []),
                    metadata=data.get("metadata", {})
                )
                prompt.performance_metrics = data.get("performance_metrics", prompt.performance_metrics)
                prompt.created_at = data.get("created_at", prompt.created_at)

                if prompt.prompt_id not in self.prompts:
                    self.prompts[prompt.prompt_id] = {}

                self.prompts[prompt.prompt_id][prompt.version] = prompt

            except Exception as e:
                print(f"Error loading prompt from {file_path}: {e}")

    def _load_experiments(self):
        """Load experiments from disk."""
        if not self.storage_path.exists():
            return

        for file_path in self.storage_path.glob("experiment_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                experiment = ABTestExperiment(
                    experiment_id=data["experiment_id"],
                    name=data["name"],
                    variants=data["variants"],
                    traffic_split=data.get("traffic_split")
                )
                experiment.results = data.get("results", experiment.results)
                experiment.created_at = data.get("created_at", experiment.created_at)
                experiment.status = data.get("status", "running")

                self.experiments[experiment.experiment_id] = experiment

            except Exception as e:
                print(f"Error loading experiment from {file_path}: {e}")
