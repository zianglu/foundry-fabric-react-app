from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class EntityListResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    raw: dict[str, Any] | None = None
