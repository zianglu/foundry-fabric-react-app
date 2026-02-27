from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException, status

from ..auth import UserContext
from ..config import Settings
from ..obo import OboTokenProvider


class FoundryAgentClient:
    def __init__(self, settings: Settings, token_provider: OboTokenProvider) -> None:
        self.settings = settings
        self.token_provider = token_provider
        self.session = requests.Session()

    def _resolve_endpoint(self) -> str:
        endpoint = self.settings.foundry_agent_endpoint
        if "{agent_id}" in endpoint:
            if not self.settings.foundry_agent_id:
                raise RuntimeError(
                    "FOUNDRY_AGENT_ENDPOINT includes '{agent_id}' but "
                    "FOUNDRY_AGENT_ID is not configured."
                )
            endpoint = endpoint.format(agent_id=self.settings.foundry_agent_id)
        return endpoint

    @staticmethod
    def _extract_answer(payload: dict[str, Any]) -> str:
        if isinstance(payload.get("answer"), str):
            return payload["answer"]

        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content

                    if isinstance(content, list):
                        text_parts: list[str] = []
                        for item in content:
                            if not isinstance(item, dict):
                                continue
                            text = item.get("text") or item.get("value")
                            if isinstance(text, str):
                                text_parts.append(text)
                        if text_parts:
                            return "\n".join(text_parts)

        data = payload.get("data")
        if isinstance(data, dict):
            nested_answer = data.get("answer")
            if isinstance(nested_answer, str):
                return nested_answer

        return "No answer returned by Foundry agent"

    def ask(
        self,
        user: UserContext,
        question: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        access_token = self.token_provider.get_access_token(
            user_assertion_token=user.access_token,
            scope=self.settings.foundry_agent_scope,
        )

        payload: dict[str, Any] = {
            "messages": [{"role": "user", "content": question}],
        }

        if self.settings.foundry_agent_id:
            payload["agent_id"] = self.settings.foundry_agent_id

        if thread_id:
            payload["thread_id"] = thread_id

        response = self.session.post(
            self._resolve_endpoint(),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=self.settings.http_timeout_seconds,
        )

        if not response.ok:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Foundry Agent request failed "
                    f"({response.status_code}): {response.text}"
                ),
            )

        if response.content:
            try:
                payload = response.json()
            except ValueError:
                payload = {"raw_text": response.text}
        else:
            payload = {}
        answer = self._extract_answer(payload)

        return {
            "answer": answer,
            "raw": payload,
        }
