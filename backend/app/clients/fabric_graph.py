from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException, status

from ..auth import UserContext
from ..config import Settings
from ..obo import OboTokenProvider


class FabricGraphClient:
    def __init__(self, settings: Settings, token_provider: OboTokenProvider) -> None:
        self.settings = settings
        self.token_provider = token_provider
        self.session = requests.Session()

    def _build_url(self, path: str) -> str:
        return f"{self.settings.fabric_graph_base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _normalize_to_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if isinstance(payload, dict):
            value = payload.get("value")
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            return [payload]

        return []

    def _get_collection(
        self,
        user: UserContext,
        path: str,
        query_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        access_token = self.token_provider.get_access_token(
            user_assertion_token=user.access_token,
            scope=self.settings.fabric_graph_scope,
        )

        response = self.session.get(
            self._build_url(path),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            params=query_params,
            timeout=self.settings.http_timeout_seconds,
        )

        if not response.ok:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Fabric Graph request failed ({response.status_code}): {response.text}"
                ),
            )

        if not response.content:
            return []

        return self._normalize_to_list(response.json())

    def list_trucks(self, user: UserContext) -> list[dict[str, Any]]:
        return self._get_collection(user, self.settings.fabric_graph_trucks_path)

    def list_drivers(self, user: UserContext) -> list[dict[str, Any]]:
        return self._get_collection(user, self.settings.fabric_graph_drivers_path)

    def list_loads(self, user: UserContext) -> list[dict[str, Any]]:
        return self._get_collection(user, self.settings.fabric_graph_loads_path)

    def list_customers(self, user: UserContext) -> list[dict[str, Any]]:
        return self._get_collection(user, self.settings.fabric_graph_customers_path)

    def query_graphql(
        self,
        user: UserContext,
        query: str,
    ) -> dict[str, Any]:
        access_token = self.token_provider.get_access_token(
            user_assertion_token=user.access_token,
            scope=self.settings.fabric_graph_scope,
        )

        response = self.session.post(
            self.settings.fabric_graphql_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"query": query},
            timeout=120,
        )

        if not response.ok:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Fabric GraphQL request failed ({response.status_code}): {response.text}"
                ),
            )

        return response.json()

    def list_terminals(self, user: UserContext) -> list[dict[str, Any]]:
        query = """query {
  terminals(first: 100) {
    items {
      name
      latitude
      longitude
    }
  }
}"""
        payload = self.query_graphql(user, query)

        import logging
        logging.getLogger(__name__).info("Fabric terminals raw response: %s", payload)

        items = (payload.get("data") or {}).get("terminals", {}).get("items", [])
        terminals: list[dict[str, Any]] = []
        for row in items:
            if isinstance(row, dict):
                name = row.get("name")
                lat = row.get("latitude")
                lon = row.get("longitude")
                if name is not None and lat is not None and lon is not None:
                    terminals.append({
                        "name": str(name),
                        "latitude": float(lat),
                        "longitude": float(lon),
                    })
        return terminals

    def list_trips(
        self,
        user: UserContext,
        status_filter: str | None = None,
        customer_id: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if status_filter:
            params["status"] = status_filter
        if customer_id:
            params["customerId"] = customer_id
        return self._get_collection(
            user,
            self.settings.fabric_graph_trips_path,
            params or None,
        )
