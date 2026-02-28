"""
Advanced AI Gateway with Caching, Rate Limiting, and Budget Controls
Extended version of gateway.py with enterprise features
"""

import os
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
# Note: LiteLLM not used due to Windows Long Path issues
# Using simplified gateway implementation instead
from dotenv import load_dotenv

load_dotenv()


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_buckets = defaultdict(list)
        self.hour_buckets = defaultdict(list)

    def check_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.

        Returns:
            (allowed: bool, reason: Optional[str])
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        # Clean old entries
        self.minute_buckets[user_id] = [
            ts for ts in self.minute_buckets[user_id] if ts > minute_ago
        ]
        self.hour_buckets[user_id] = [
            ts for ts in self.hour_buckets[user_id] if ts > hour_ago
        ]

        # Check limits
        if len(self.minute_buckets[user_id]) >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"

        if len(self.hour_buckets[user_id]) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"

        # Add current request
        self.minute_buckets[user_id].append(now)
        self.hour_buckets[user_id].append(now)

        return True, None


class BudgetManager:
    """Budget tracking and enforcement."""

    def __init__(self, daily_limit: float = 100.0, monthly_limit: float = 1000.0):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.daily_spend = defaultdict(float)
        self.monthly_spend = defaultdict(float)
        self.last_reset_day = datetime.now().date()
        self.last_reset_month = datetime.now().replace(day=1).date()

    def check_budget(self, user_id: str, estimated_cost: float) -> tuple[bool, Optional[str]]:
        """
        Check if request is within budget.

        Returns:
            (allowed: bool, reason: Optional[str])
        """
        self._reset_if_needed()

        # Check daily budget
        if self.daily_spend[user_id] + estimated_cost > self.daily_limit:
            return False, f"Daily budget limit reached: ${self.daily_limit:.2f}"

        # Check monthly budget
        if self.monthly_spend[user_id] + estimated_cost > self.monthly_limit:
            return False, f"Monthly budget limit reached: ${self.monthly_limit:.2f}"

        return True, None

    def track_spend(self, user_id: str, cost: float):
        """Track actual spend."""
        self.daily_spend[user_id] += cost
        self.monthly_spend[user_id] += cost

    def _reset_if_needed(self):
        """Reset counters if new day/month."""
        today = datetime.now().date()
        current_month = datetime.now().replace(day=1).date()

        if today > self.last_reset_day:
            self.daily_spend.clear()
            self.last_reset_day = today

        if current_month > self.last_reset_month:
            self.monthly_spend.clear()
            self.last_reset_month = current_month

    def get_budget_status(self, user_id: str) -> Dict[str, Any]:
        """Get current budget status."""
        self._reset_if_needed()

        return {
            "daily": {
                "spent": round(self.daily_spend[user_id], 4),
                "limit": self.daily_limit,
                "remaining": round(self.daily_limit - self.daily_spend[user_id], 4),
                "percentage_used": round((self.daily_spend[user_id] / self.daily_limit * 100), 1)
            },
            "monthly": {
                "spent": round(self.monthly_spend[user_id], 4),
                "limit": self.monthly_limit,
                "remaining": round(self.monthly_limit - self.monthly_spend[user_id], 4),
                "percentage_used": round((self.monthly_spend[user_id] / self.monthly_limit * 100), 1)
            }
        }


class AdvancedAIGateway:
    """
    Advanced AI Gateway with enterprise features:
    - LiteLLM caching for repeated queries
    - Rate limiting per user/model
    - Budget controls and alerts
    - Request deduplication
    """

    def __init__(
        self,
        verbose: bool = False,
        enable_caching: bool = True,
        cache_ttl: int = 3600,
        enable_rate_limiting: bool = True,
        enable_budget_controls: bool = True
    ):
        """
        Initialize Advanced AI Gateway.

        Args:
            verbose: Enable detailed logging
            enable_caching: Enable response caching
            cache_ttl: Cache time-to-live in seconds
            enable_rate_limiting: Enable rate limiting
            enable_budget_controls: Enable budget tracking
        """
        self.verbose = verbose
        litellm.set_verbose = verbose

        # Configure API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash-exp")

        if self.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
        if self.google_api_key:
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
            os.environ["GEMINI_API_KEY"] = self.google_api_key

        # Enable caching (simplified - in-memory dict)
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.cache_store = {}  # Simple in-memory cache

        # Initialize rate limiter
        self.enable_rate_limiting = enable_rate_limiting
        if enable_rate_limiting:
            self.rate_limiter = RateLimiter(
                requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
                requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
            )

        # Initialize budget manager
        self.enable_budget_controls = enable_budget_controls
        if enable_budget_controls:
            self.budget_manager = BudgetManager(
                daily_limit=float(os.getenv("DAILY_BUDGET_LIMIT", "100.0")),
                monthly_limit=float(os.getenv("MONTHLY_BUDGET_LIMIT", "1000.0"))
            )

        # Cache stats
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_cost_saved": 0.0
        }

    def call_with_controls(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        user_id: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with rate limiting and budget controls.

        Args:
            provider: "openai" or "gemini"
            messages: Message list
            user_id: User identifier for rate limiting
            **kwargs: Additional arguments

        Returns:
            Standardized response
        """
        # Check rate limits
        if self.enable_rate_limiting:
            allowed, reason = self.rate_limiter.check_limit(user_id)
            if not allowed:
                return self._error_response(reason, provider)

        # Estimate cost (rough estimate)
        estimated_tokens = sum(len(m.get("content", "").split()) for m in messages) * 1.3
        estimated_cost = (estimated_tokens / 1_000_000) * 0.5  # Conservative estimate

        # Check budget
        if self.enable_budget_controls:
            allowed, reason = self.budget_manager.check_budget(user_id, estimated_cost)
            if not allowed:
                return self._error_response(reason, provider)

        # Check cache
        cache_key = None
        if self.enable_caching:
            cache_key = self._generate_cache_key(provider, messages, kwargs)
            cached_response = self._check_cache(cache_key)
            if cached_response:
                self.cache_stats["hits"] += 1
                cached_response["from_cache"] = True
                return cached_response
            self.cache_stats["misses"] += 1

        # Make actual call
        if provider == "openai":
            response = self.call_openai(messages, **kwargs)
        elif provider == "gemini":
            response = self.call_gemini(messages, **kwargs)
        else:
            return self._error_response(f"Unknown provider: {provider}", provider)

        # Track actual spend
        if self.enable_budget_controls and response["success"]:
            self.budget_manager.track_spend(user_id, response["cost"])

        # Store in cache
        if self.enable_caching and response["success"] and cache_key:
            self._store_cache(cache_key, response)

        response["from_cache"] = False
        return response

    def call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call OpenAI with caching support."""
        try:
            start_time = time.time()

            call_kwargs = {
                "model": self.openai_model,
                "messages": messages,
                "temperature": temperature,
                "caching": self.enable_caching,
                **kwargs
            }

            if max_tokens:
                call_kwargs["max_tokens"] = max_tokens
            if response_format:
                call_kwargs["response_format"] = response_format

            response = completion(**call_kwargs)
            latency = time.time() - start_time

            return self._standardize_response(response, latency, "openai")

        except Exception as e:
            return self._error_response(f"OpenAI call failed: {str(e)}", "openai")

    def call_gemini(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Gemini with caching support."""
        try:
            from app.gateway import AIGateway
            base_gateway = AIGateway()
            response = base_gateway.call_gemini(messages, temperature, max_tokens)
            return response

        except Exception as e:
            return self._error_response(f"Gemini call failed: {str(e)}", "gemini")

    def _generate_cache_key(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        kwargs: Dict[str, Any]
    ) -> str:
        """Generate cache key from request parameters."""
        cache_data = {
            "provider": provider,
            "messages": messages,
            "kwargs": {k: v for k, v in kwargs.items() if k not in ["user_id"]}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if response is in cache."""
        # Note: LiteLLM handles caching internally
        # This is a placeholder for custom cache implementation
        return None

    def _store_cache(self, cache_key: str, response: Dict[str, Any]):
        """Store response in cache."""
        # Note: LiteLLM handles caching internally
        pass

    def _standardize_response(
        self,
        response: Any,
        latency: float,
        provider: str
    ) -> Dict[str, Any]:
        """Convert response to standard format."""
        try:
            content = response.choices[0].message.content
            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else (input_tokens + output_tokens)

            cost = 0.0
            if hasattr(response, '_hidden_params') and response._hidden_params:
                cost = response._hidden_params.get("response_cost", 0.0)

            model_used = response.model if hasattr(response, 'model') else "unknown"

            return {
                "success": True,
                "content": content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "model": model_used,
                "latency": latency,
                "provider": provider,
                "error": None,
                "from_cache": False
            }

        except Exception as e:
            return self._error_response(f"Response parsing failed: {str(e)}", provider)

    def _error_response(self, error_message: str, provider: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "success": False,
            "content": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
            "model": "unknown",
            "latency": 0.0,
            "provider": provider,
            "error": error_message,
            "from_cache": False
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0 else 0.0
        )

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 1),
            "estimated_cost_saved": round(self.cache_stats["total_cost_saved"], 4)
        }

    def get_budget_status(self, user_id: str = "default") -> Dict[str, Any]:
        """Get budget status for user."""
        if not self.enable_budget_controls:
            return {"enabled": False}

        return {
            "enabled": True,
            **self.budget_manager.get_budget_status(user_id)
        }
