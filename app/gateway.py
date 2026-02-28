"""
AI Gateway - Unified LLM Interface (Simplified for Windows)
Direct OpenAI and Gemini integration without LiteLLM dependency
"""

import os
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIGateway:
    """
    Unified AI Gateway for OpenAI and Gemini.

    Features:
    - Direct SDK integration (no LiteLLM dependency)
    - Automatic cost tracking and token counting
    - Standardized response format
    - Windows-compatible
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize AI Gateway.

        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose

        # Configure API keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

        # Model configurations
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        # Initialize clients
        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        if GEMINI_AVAILABLE and self.google_api_key:
            genai.configure(api_key=self.google_api_key)
        else:
            pass  # Gemini not configured

        # Cost tracking (per 1M tokens)
        self.cost_per_token = {
            "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.6 / 1_000_000},
            "gpt-4o": {"input": 2.5 / 1_000_000, "output": 10.0 / 1_000_000},
            "gemini-2.0-flash": {"input": 0.075 / 1_000_000, "output": 0.3 / 1_000_000},
            "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free during preview
        }

    def call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Additional arguments

        Returns:
            Standardized response dictionary
        """
        if not self.openai_client:
            return self._error_response("OpenAI not configured. Add OPENAI_API_KEY to .env", "openai")

        try:
            start_time = time.time()

            call_kwargs = {
                "model": self.openai_model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                call_kwargs["max_tokens"] = max_tokens
            if response_format:
                call_kwargs["response_format"] = response_format

            response = self.openai_client.chat.completions.create(**call_kwargs)

            latency = time.time() - start_time

            return self._standardize_openai_response(response, latency)

        except Exception as e:
            return self._error_response(f"OpenAI call failed: {str(e)}", "openai")

    def call_gemini(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Gemini model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments

        Returns:
            Standardized response dictionary
        """
        if not GEMINI_AVAILABLE:
            return self._error_response("Gemini SDK not installed. Run: pip install google-generativeai", "gemini")

        if not self.google_api_key:
            return self._error_response("Gemini not configured. Add GOOGLE_API_KEY to .env", "gemini")

        try:
            start_time = time.time()

            # Convert messages to Gemini format
            gemini_messages = self._convert_to_gemini_format(messages)

            # Create model
            model = genai.GenerativeModel(
                model_name=self.gemini_model.replace("gemini/", ""),
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens or 2048,
                }
            )

            # Generate response
            response = model.generate_content(gemini_messages)

            latency = time.time() - start_time

            return self._standardize_gemini_response(response, latency)

        except Exception as e:
            return self._error_response(f"Gemini call failed: {str(e)}", "gemini")

    def _convert_to_gemini_format(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Gemini prompt."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"Instructions: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)

    def _standardize_openai_response(
        self,
        response: Any,
        latency: float
    ) -> Dict[str, Any]:
        """Convert OpenAI response to standardized format."""
        try:
            content = response.choices[0].message.content
            usage = response.usage

            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else (input_tokens + output_tokens)

            # Calculate cost
            model_key = "gpt-4o-mini" if "mini" in self.openai_model else "gpt-4o"
            cost_info = self.cost_per_token.get(model_key, self.cost_per_token["gpt-4o-mini"])
            cost = (input_tokens * cost_info["input"]) + (output_tokens * cost_info["output"])

            return {
                "success": True,
                "content": content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "model": self.openai_model,
                "latency": latency,
                "provider": "openai",
                "error": None
            }

        except Exception as e:
            return self._error_response(f"Response parsing failed: {str(e)}", "openai")

    def _standardize_gemini_response(
        self,
        response: Any,
        latency: float
    ) -> Dict[str, Any]:
        """Convert Gemini response to standardized format."""
        try:
            content = response.text

            # Gemini doesn't always provide token counts
            input_tokens = getattr(response, 'prompt_token_count', 0)
            output_tokens = getattr(response, 'candidates_token_count', 0) if hasattr(response, 'candidates_token_count') else len(content.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)

            # Calculate cost (free during preview)
            cost = 0.0

            return {
                "success": True,
                "content": content,
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": total_tokens,
                "cost": cost,
                "model": self.gemini_model,
                "latency": latency,
                "provider": "gemini",
                "error": None
            }

        except Exception as e:
            return self._error_response(f"Response parsing failed: {str(e)}", "gemini")

    def _error_response(self, error_message: str, provider: str) -> Dict[str, Any]:
        """Create standardized error response."""
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
            "error": error_message
        }

    def get_available_models(self) -> Dict[str, bool]:
        """Check which models are available."""
        return {
            "openai": bool(self.openai_client),
            "gemini": GEMINI_AVAILABLE and bool(self.google_api_key)
        }

    async def call_openai_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version - calls sync for now."""
        return self.call_openai(messages, temperature, max_tokens, response_format, **kwargs)

    async def call_gemini_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version - calls sync for now."""
        return self.call_gemini(messages, temperature, max_tokens, **kwargs)
