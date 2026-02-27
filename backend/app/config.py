from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "foundry-fabric-backend"
    environment: str = "dev"
    log_level: str = "INFO"

    azure_tenant_id: str = Field(..., alias="AZURE_TENANT_ID")
    backend_client_id: str = Field(..., alias="BACKEND_CLIENT_ID")
    backend_api_audience: str | None = Field(default=None, alias="BACKEND_API_AUDIENCE")
    backend_allowed_audiences: str | None = Field(default=None, alias="BACKEND_ALLOWED_AUDIENCES")
    backend_required_scope: str = Field(default="access_as_user", alias="BACKEND_REQUIRED_SCOPE")

    backend_client_secret: str | None = Field(default=None, alias="BACKEND_CLIENT_SECRET")
    backend_client_certificate_path: str | None = Field(default=None, alias="BACKEND_CLIENT_CERTIFICATE_PATH")
    backend_client_certificate_thumbprint: str | None = Field(default=None, alias="BACKEND_CLIENT_CERTIFICATE_THUMBPRINT")

    foundry_agent_endpoint: str = Field(..., alias="FOUNDRY_AGENT_ENDPOINT")
    foundry_agent_scope: str = Field(default="https://ai.azure.com/.default", alias="FOUNDRY_AGENT_SCOPE")
    foundry_agent_id: str | None = Field(default=None, alias="FOUNDRY_AGENT_ID")

    fabric_graph_base_url: str = Field(..., alias="FABRIC_GRAPH_BASE_URL")
    fabric_graph_scope: str = Field(default="https://api.fabric.microsoft.com/.default", alias="FABRIC_GRAPH_SCOPE")
    fabric_graph_trucks_path: str = Field(default="/trucks", alias="FABRIC_GRAPH_TRUCKS_PATH")
    fabric_graph_drivers_path: str = Field(default="/drivers", alias="FABRIC_GRAPH_DRIVERS_PATH")
    fabric_graph_loads_path: str = Field(default="/loads", alias="FABRIC_GRAPH_LOADS_PATH")
    fabric_graph_trips_path: str = Field(default="/trips", alias="FABRIC_GRAPH_TRIPS_PATH")
    fabric_graph_customers_path: str = Field(default="/customers", alias="FABRIC_GRAPH_CUSTOMERS_PATH")

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    http_timeout_seconds: int = Field(default=30, alias="HTTP_TIMEOUT_SECONDS")

    @property
    def allowed_audiences(self) -> list[str]:
        if self.backend_allowed_audiences:
            values = [value.strip() for value in self.backend_allowed_audiences.split(",") if value.strip()]
            if values:
                return values

        if self.backend_api_audience:
            return [self.backend_api_audience]

        return [f"api://{self.backend_client_id}", self.backend_client_id]

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
