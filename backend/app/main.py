from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .auth import UserContext, get_user_context
from .clients.fabric_graph import FabricGraphClient
from .clients.foundry import FoundryAgentClient
from .config import Settings, get_settings
from .models import ChatRequest, ChatResponse, EntityListResponse, HealthResponse
from .obo import OboTokenProvider


@lru_cache
def get_obo_provider() -> OboTokenProvider:
    settings = get_settings()
    return OboTokenProvider(settings)


@lru_cache
def get_graph_client() -> FabricGraphClient:
    settings = get_settings()
    token_provider = get_obo_provider()
    return FabricGraphClient(settings, token_provider)


@lru_cache
def get_foundry_client() -> FoundryAgentClient:
    settings = get_settings()
    token_provider = get_obo_provider()
    return FoundryAgentClient(settings, token_provider)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/api/trucks", response_model=EntityListResponse)
def get_trucks(
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(items=graph_client.list_trucks(user))


@app.get("/api/terminals", response_model=EntityListResponse)
def get_terminals(
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(items=graph_client.list_terminals(user))


@app.get("/api/drivers", response_model=EntityListResponse)
def get_drivers(
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(items=graph_client.list_drivers(user))


@app.get("/api/loads", response_model=EntityListResponse)
def get_loads(
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(items=graph_client.list_loads(user))


@app.get("/api/customers", response_model=EntityListResponse)
def get_customers(
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(items=graph_client.list_customers(user))


@app.get("/api/trips", response_model=EntityListResponse)
def get_trips(
    status_filter: str | None = Query(default=None, alias="status"),
    customer_id: str | None = Query(default=None, alias="customerId"),
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(
        items=graph_client.list_trips(
            user,
            status_filter=status_filter,
            customer_id=customer_id,
        )
    )


@app.get("/api/customers/{customer_id}/active-trips", response_model=EntityListResponse)
def get_active_trips_for_customer(
    customer_id: str,
    user: UserContext = Depends(get_user_context),
    graph_client: FabricGraphClient = Depends(get_graph_client),
) -> EntityListResponse:
    return EntityListResponse(
        items=graph_client.list_trips(
            user,
            status_filter="active",
            customer_id=customer_id,
        )
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: UserContext = Depends(get_user_context),
    foundry_client: FoundryAgentClient = Depends(get_foundry_client),
) -> ChatResponse:
    result = foundry_client.ask(
        user=user,
        question=request.question,
        thread_id=request.thread_id,
    )
    return ChatResponse(
        answer=result["answer"],
        thread_id=result.get("thread_id"),
        raw=result.get("raw"),
    )
