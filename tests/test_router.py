"""
Unit tests for LLM Router
"""
import pytest
from app.router import LLMRouter
from app.models.task import Task, TaskType


class TestLLMRouter:
    """Test suite for intelligent routing logic"""

    @pytest.fixture
    def router(self):
        """Create router instance for testing"""
        return LLMRouter()

    def test_router_strict_json_routes_to_openai(self, router):
        """Test: Tasks requiring strict JSON should route to OpenAI"""
        task = Task(
            description="Analyze transaction",
            requires_strict_json=True,
            context_length=1000,
            business_impact=0.5
        )

        result = router.route(task)
        assert result == "openai"

        reason = router.get_routing_reason(task)
        assert "json" in reason.lower() and "openai" in reason.lower()

    def test_router_long_context_routes_to_gemini(self, router):
        """Test: Large context (>80k tokens) should route to Gemini"""
        task = Task(
            description="Analyze 500-page document",
            requires_strict_json=False,
            context_length=100000,  # > 80k threshold
            business_impact=0.5
        )

        result = router.route(task)
        assert result == "gemini"

        reason = router.get_routing_reason(task)
        assert "context" in reason.lower()

    def test_router_multi_document_routes_to_gemini(self, router):
        """Test: Multi-document analysis should route to Gemini"""
        task = Task(
            description="Cross-reference 50 documents",
            multi_document=True,
            context_length=5000,
            business_impact=0.5
        )

        result = router.route(task)
        assert result == "gemini"

        reason = router.get_routing_reason(task)
        assert "multi-document" in reason.lower()

    def test_router_high_impact_routes_to_ensemble(self, router):
        """Test: High business impact (>0.8) should route to Ensemble"""
        task = Task(
            description="$500,000 wire transfer approval",
            requires_strict_json=False,
            context_length=2000,
            business_impact=0.95  # > 0.8 threshold
        )

        result = router.route(task)
        assert result == "ensemble"

        reason = router.get_routing_reason(task)
        assert "high impact" in reason.lower() or "ensemble" in reason.lower()

    def test_router_default_routes_to_openai(self, router):
        """Test: Default case should route to OpenAI"""
        task = Task(
            description="Standard fraud check",
            requires_strict_json=False,
            context_length=1500,
            multi_document=False,
            business_impact=0.5
        )

        result = router.route(task)
        assert result == "openai"

    def test_router_priority_strict_json_over_long_context(self, router):
        """Test: Strict JSON requirement should take priority over context length"""
        task = Task(
            description="Extract structured data from long document",
            requires_strict_json=True,  # Priority rule
            context_length=100000,      # Would normally go to Gemini
            business_impact=0.5
        )

        result = router.route(task)
        assert result == "openai"

    def test_router_reasoning_explanation(self, router):
        """Test: Router should provide human-readable explanations"""
        task = Task(
            description="Test task",
            requires_strict_json=True,
            context_length=1000,
            business_impact=0.5
        )

        reason = router.get_routing_reason(task)

        # Should contain explanation text
        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "OpenAI" in reason or "Gemini" in reason or "Ensemble" in reason

    def test_router_edge_case_exact_threshold(self, router):
        """Test: Exact threshold values (boundary testing)"""
        # Test context length exactly at threshold
        task_at_threshold = Task(
            description="Test at threshold",
            context_length=80000,  # Exactly at threshold
            business_impact=0.5
        )

        result = router.route(task_at_threshold)
        # At threshold, should NOT exceed, so OpenAI
        assert result == "openai"

        # Test business impact exactly at threshold
        task_impact_threshold = Task(
            description="Test impact threshold",
            context_length=1000,
            business_impact=0.8  # Exactly at threshold
        )

        result2 = router.route(task_impact_threshold)
        # At threshold, should NOT trigger ensemble
        assert result2 == "openai"
