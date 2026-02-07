"""LLM Gateway service.

Provides unified interface for multiple LLM providers (OpenAI, Anthropic).
"""

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings


logger = structlog.get_logger()


class LLMGateway:
    """Multi-provider LLM gateway.

    Supports OpenAI and Anthropic with automatic retry logic.

    Usage:
        gateway = LLMGateway()
        response = await gateway.generate("Hello, how can I help?")
    """

    def __init__(self, provider: Optional[str] = None):
        """Initialize LLM gateway.

        Args:
            provider: LLM provider ("openai" or "anthropic").
                     Defaults to settings.llm_provider.
        """
        self.provider = provider or settings.llm_provider

        if self.provider == "openai":
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            self._anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt/message.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0-1).
            system_prompt: Optional system message.

        Returns:
            Generated text response.
        """
        logger.info(
            "llm_generate_start",
            provider=self.provider,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
        )

        if self.provider == "openai":
            return await self._generate_openai(
                prompt, max_tokens, temperature, system_prompt
            )
        else:
            return await self._generate_anthropic(
                prompt, max_tokens, temperature, system_prompt
            )

    async def _generate_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> str:
        """Generate response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        content = response.choices[0].message.content
        logger.info(
            "llm_generate_complete",
            provider="openai",
            tokens_used=response.usage.total_tokens if response.usage else 0,
        )
        return content or ""

    async def _generate_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str],
    ) -> str:
        """Generate response using Anthropic."""
        response = await self._anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text if response.content else ""
        logger.info(
            "llm_generate_complete",
            provider="anthropic",
            tokens_used=response.usage.input_tokens + response.usage.output_tokens
            if response.usage
            else 0,
        )
        return content

    async def generate_with_history(
        self,
        messages: list[dict],
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate response with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            system_prompt: Optional system message.

        Returns:
            Generated text response.
        """
        if self.provider == "openai":
            all_messages = []
            if system_prompt:
                all_messages.append({"role": "system", "content": system_prompt})
            all_messages.extend(messages)

            response = await self._openai.chat.completions.create(
                model="gpt-4o",
                messages=all_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        else:
            # Anthropic format
            anthropic_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m["role"] in ("user", "assistant")
            ]

            response = await self._anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=anthropic_messages,
            )
            return response.content[0].text if response.content else ""
