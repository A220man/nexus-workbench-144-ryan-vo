"""Chat/completion endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    id: str
    model: str
    choices: List[dict]
    usage: dict


@router.post("/completions", response_model=ChatResponse)
async def create_completion(request: ChatRequest):
    """Create a chat completion."""
    if request.stream:
        raise HTTPException(status_code=501, detail="Streaming not yet implemented")

    # Placeholder response
    return {
        "id": "cmpl-placeholder",
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a placeholder response. The inference engine is not yet connected."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


@router.post("/completions/stream")
async def create_completion_stream(request: ChatRequest):
    """Create a streaming chat completion."""
    async def event_generator():
        yield {"data": "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\n"}
        await asyncio.sleep(0.1)
        yield {"data": "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\n\n"}
        await asyncio.sleep(0.1)
        yield {"data": "data: [DONE]\n\n"}

    return EventSourceResponse(event_generator())
