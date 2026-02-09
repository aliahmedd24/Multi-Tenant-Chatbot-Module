"""LLM gateway abstraction with mock and OpenAI backends."""

from app.config import get_settings


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> dict:
    """Generate a response from the LLM.

    Args:
        prompt: The user prompt/question
        system_prompt: Optional system instructions
        model: Optional model override

    Returns:
        dict with keys: response, prompt_tokens, completion_tokens, total_tokens
    """
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "mock":
        return _mock_response(prompt)

    if provider == "openai":
        return _openai_response(prompt, system_prompt, model)

    raise ValueError(f"Unknown LLM provider: {provider}")


def _mock_response(prompt: str) -> dict:
    """Generate a deterministic mock response for testing."""
    # Create a response based on the prompt content
    if "hours" in prompt.lower():
        response = "Our business hours are Monday to Friday, 9 AM to 5 PM."
    elif "menu" in prompt.lower():
        response = "Our menu includes a variety of dishes. Please visit our website for the full menu."
    elif "location" in prompt.lower():
        response = "We are located at 123 Main Street, Downtown."
    else:
        response = f"Based on the available information: This is a mock response to your query about '{prompt[:50]}...'"

    # Mock token counts
    prompt_tokens = len(prompt.split())
    completion_tokens = len(response.split())

    return {
        "response": response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def _openai_response(
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> dict:
    """Generate response using OpenAI API."""
    import openai

    settings = get_settings()
    client = openai.OpenAI(api_key=settings.openai_api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
    )

    choice = response.choices[0]
    usage = response.usage

    return {
        "response": choice.message.content or "",
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
    }
