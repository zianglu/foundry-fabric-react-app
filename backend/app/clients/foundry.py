from __future__ import annotations

import time
from typing import Any

from azure.ai.agents.models import ListSortOrder
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken
from fastapi import HTTPException, status

from ..auth import UserContext
from ..config import Settings
from ..obo import OboTokenProvider


class _OboCredential:
    """TokenCredential that delegates to OboTokenProvider for each scope."""

    def __init__(self, obo_provider: OboTokenProvider, user_assertion: str) -> None:
        self._obo_provider = obo_provider
        self._user_assertion = user_assertion

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        scope = scopes[0] if scopes else "https://ai.azure.com/.default"
        token = self._obo_provider.get_access_token(self._user_assertion, scope)
        return AccessToken(token, int(time.time()) + 3600)


class FoundryAgentClient:
    def __init__(self, settings: Settings, token_provider: OboTokenProvider) -> None:
        self.settings = settings
        self.token_provider = token_provider

    def ask(
        self,
        user: UserContext,
        question: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        credential = _OboCredential(self.token_provider, user.access_token)
        client = AIProjectClient(
            credential=credential,
            endpoint=self.settings.foundry_agent_endpoint,
        )

        agent_id = self.settings.foundry_agent_id
        if not agent_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="FOUNDRY_AGENT_ID is not configured.",
            )

        # Reuse existing thread or create a new one
        if thread_id:
            thread = client.agents.threads.get(thread_id)
        else:
            thread = client.agents.threads.create()

        # Post the user message
        client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=question,
        )

        # Run the agent synchronously
        run = client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent_id,
        )

        if run.status == "failed":
            error_detail = str(run.last_error) if run.last_error else "unknown error"
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Foundry Agent run failed: {error_detail}",
            )

        # Read the assistant's reply
        messages = client.agents.messages.list(
            thread_id=thread.id,
            order=ListSortOrder.ASCENDING,
        )

        answer = "No answer returned by Foundry agent"
        for msg in messages:
            if msg.role == "assistant" and msg.text_messages:
                answer = msg.text_messages[-1].text.value

        return {
            "answer": answer,
            "thread_id": thread.id,
        }
