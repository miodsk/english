import asyncio
from unittest.mock import Mock, AsyncMock
from src.services.langchain.llm import AIService


# Mock the LLM and TTS for testing
async def test_streaming_architecture():
    """Test the simplified streaming architecture"""
    # Create mock LLM
    mock_llm = Mock()
    mock_chunk1 = Mock(content="Hello")
    mock_chunk2 = Mock(content=" world!")
    mock_llm.astream = AsyncMock(return_value=[mock_chunk1, mock_chunk2])

    # Create mock TTS
    mock_tts = Mock()
    mock_tts.streaming_call = AsyncMock()
    mock_tts.streaming_complete = AsyncMock()
    mock_tts.audio_generator = AsyncMock(
        return_value=[b"audio_data_1", b"audio_data_2"]
    )
    mock_tts.start_session = AsyncMock()
    mock_tts.close = AsyncMock()

    # Create AI service with mocks
    ai_service = AIService(llm=mock_llm)
    ai_service.tts = mock_tts

    # Test streaming
    message = "Test message"
    results = []
    async for item in ai_service.get_chat_stream(message):
        results.append(item)

    print(f"Stream returned {len(results)} items")
    print("Test completed successfully")


if __name__ == "__main__":
    asyncio.run(test_streaming_architecture())
