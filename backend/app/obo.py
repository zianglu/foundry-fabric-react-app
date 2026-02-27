from __future__ import annotations

from pathlib import Path

import msal
from fastapi import HTTPException, status

from .config import Settings


class OboTokenProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._app = msal.ConfidentialClientApplication(
            client_id=settings.backend_client_id,
            authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
            client_credential=self._build_client_credential(),
        )

    def _build_client_credential(self) -> str | dict[str, str]:
        if self.settings.backend_client_secret:
            return self.settings.backend_client_secret

        if self.settings.backend_client_certificate_path and self.settings.backend_client_certificate_thumbprint:
            certificate_path = Path(self.settings.backend_client_certificate_path)
            if not certificate_path.exists():
                raise RuntimeError(
                    "BACKEND_CLIENT_CERTIFICATE_PATH does not exist: "
                    f"{certificate_path}"
                )

            private_key = certificate_path.read_text(encoding="utf-8")
            return {
                "private_key": private_key,
                "thumbprint": self.settings.backend_client_certificate_thumbprint,
            }

        raise RuntimeError(
            "Configure BACKEND_CLIENT_SECRET for local development or "
            "BACKEND_CLIENT_CERTIFICATE_PATH + BACKEND_CLIENT_CERTIFICATE_THUMBPRINT "
            "for non-secret deployments."
        )

    def get_access_token(self, user_assertion_token: str, scope: str) -> str:
        result = self._app.acquire_token_on_behalf_of(
            user_assertion=user_assertion_token,
            scopes=[scope],
        )

        access_token = result.get("access_token")
        if access_token:
            return access_token

        message = result.get("error_description") or str(result)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OBO token exchange failed for scope '{scope}': {message}",
        )
