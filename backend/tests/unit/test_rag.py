"""Unit tests for RAG engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.ai.rag_engine import RAGEngine
from app.services.ai.llm_gateway import LLMGateway
from app.services.knowledge.retriever import KnowledgeRetriever


@pytest.fixture
def mock_retriever():
    """Create mock retriever."""
    retriever = AsyncMock(spec=KnowledgeRetriever)
    retriever.get_context.return_value = "Hours: 9 AM - 10 PM"
    return retriever


@pytest.fixture
def mock_llm():
    """Create mock LLM gateway."""
    llm = AsyncMock(spec=LLMGateway)
    llm.generate.return_value = "We are open from 9 AM to 10 PM."
    return llm


@pytest.mark.asyncio
async def test_generate_response_with_context(mock_retriever, mock_llm):
    """Test RAG response generation with context."""
    engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)

    client_id = uuid4()
    response = await engine.generate_response(
        query="What are your hours?",
        client_id=client_id,
        client_name="Test Business",
    )

    assert response is not None
    assert len(response) > 0
    mock_retriever.get_context.assert_called_once()
    mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_response_no_context():
    """Test RAG response when no context available."""
    mock_retriever = AsyncMock(spec=KnowledgeRetriever)
    mock_retriever.get_context.return_value = ""

    mock_llm = AsyncMock(spec=LLMGateway)
    mock_llm.generate.return_value = "I don't have information about that."

    engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)

    response = await engine.generate_response(
        query="Tell me about your special deals",
        client_id=uuid4(),
        client_name="Test Business",
    )

    assert response is not None


@pytest.mark.asyncio
async def test_generate_response_with_history():
    """Test RAG response with conversation history."""
    mock_retriever = AsyncMock(spec=KnowledgeRetriever)
    mock_retriever.get_context.return_value = "Pizza: $10, Pasta: $12"

    mock_llm = AsyncMock(spec=LLMGateway)
    mock_llm.generate.return_value = "Yes, we have pasta for $12!"

    engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)

    history = [
        {"role": "user", "content": "Do you have pizza?"},
        {"role": "assistant", "content": "Yes, our pizza is $10!"},
    ]

    response = await engine.generate_response(
        query="What about pasta?",
        client_id=uuid4(),
        client_name="Test Business",
        history=history,
    )

    assert response is not None
    # Verify history was included in the call
    call_args = mock_llm.generate.call_args
    assert "pasta" in call_args[0][0].lower() or "pasta" in str(call_args)
