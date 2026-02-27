from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import Settings, get_settings


bearer_scheme = HTTPBearer(auto_error=True)


@dataclass
class UserContext:
    access_token: str
    claims: dict[str, Any]

    @property
    def object_id(self) -> str | None:
        return self.claims.get("oid")

    @property
    def principal_name(self) -> str | None:
        return self.claims.get("preferred_username") or self.claims.get("upn")


class EntraTokenValidator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session = requests.Session()
        self._jwk_client: PyJWKClient | None = None
        self._issuer: str | None = None

    @property
    def _openid_configuration_url(self) -> str:
        return (
            f"https://login.microsoftonline.com/{self.settings.azure_tenant_id}/v2.0/"
            ".well-known/openid-configuration"
        )

    def _bootstrap_metadata(self) -> None:
        if self._jwk_client and self._issuer:
            return

        response = self._session.get(
            self._openid_configuration_url,
            timeout=self.settings.http_timeout_seconds,
        )

        if not response.ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Failed to load Entra OpenID metadata "
                    f"({response.status_code}: {response.text})"
                ),
            )

        payload = response.json()
        jwks_uri = payload.get("jwks_uri")
        issuer = payload.get("issuer")

        if not jwks_uri or not issuer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenID metadata response missing jwks_uri or issuer",
            )

        self._jwk_client = PyJWKClient(jwks_uri)
        self._issuer = issuer

    def validate(self, token: str) -> dict[str, Any]:
        self._bootstrap_metadata()

        assert self._jwk_client is not None
        assert self._issuer is not None

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.allowed_audiences,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "nbf"]},
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid bearer token: {exc}",
            ) from exc

        required_scope = self.settings.backend_required_scope.strip()
        if required_scope:
            token_scopes = str(claims.get("scp", "")).split()
            token_roles = claims.get("roles", []) if isinstance(claims.get("roles"), list) else []
            if required_scope not in token_scopes and required_scope not in token_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Token is missing required delegated scope/role "
                        f"'{required_scope}'."
                    ),
                )

        return claims


@lru_cache
def get_token_validator() -> EntraTokenValidator:
    settings = get_settings()
    return EntraTokenValidator(settings)


def get_user_context(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    validator: EntraTokenValidator = Depends(get_token_validator),
) -> UserContext:
    token = credentials.credentials
    claims = validator.validate(token)
    return UserContext(access_token=token, claims=claims)
