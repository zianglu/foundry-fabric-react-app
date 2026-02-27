#!/usr/bin/env python3
"""Create or update an Azure AI Foundry agent configured with:
- Fabric Data Agent knowledge source
- Azure AI Search (PDF index) knowledge source

The script uses Entra identity (DefaultAzureCredential) and does not require static API keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.parse import urlencode

import requests
from azure.identity import DefaultAzureCredential


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update an Azure AI Foundry agent")

    parser.add_argument(
        "--agents-base-url",
        required=True,
        help=(
            "Foundry agents endpoint without trailing slash. Example: "
            "https://<project>.services.ai.azure.com/api/projects/<project-id>/agents"
        ),
    )
    parser.add_argument("--api-version", default="2025-05-15-preview")
    parser.add_argument("--scope", default="https://ai.azure.com/.default")

    parser.add_argument("--name", required=True, help="Agent name")
    parser.add_argument("--model", required=True, help="Model/deployment name")
    parser.add_argument("--description", default="Routing assistant for trucking operations")
    parser.add_argument(
        "--instructions",
        default=(
            "You are a logistics analyst. Use Fabric Data Agent for enterprise data, "
            "and use Azure AI Search index for PDF policy/procedure content. "
            "Combine both when needed and cite the source type you used."
        ),
    )

    parser.add_argument("--fabric-workspace-id", required=True)
    parser.add_argument("--fabric-data-agent-id", required=True)

    parser.add_argument("--search-connection-id", required=True)
    parser.add_argument("--search-index-name", required=True)
    parser.add_argument("--search-content-field", default="content")
    parser.add_argument("--search-title-field", default="title")

    parser.add_argument(
        "--agent-id",
        default=None,
        help="If provided, update this existing agent instead of creating a new one",
    )
    parser.add_argument("--dry-run", action="store_true")

    return parser.parse_args()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "name": args.name,
        "model": args.model,
        "description": args.description,
        "instructions": args.instructions,
        "knowledge_sources": [
            {
                "type": "fabric_data_agent",
                "workspace_id": args.fabric_workspace_id,
                "data_agent_id": args.fabric_data_agent_id,
            },
            {
                "type": "azure_ai_search",
                "connection_id": args.search_connection_id,
                "index_name": args.search_index_name,
                "fields_mapping": {
                    "content_fields": [args.search_content_field],
                    "title_field": args.search_title_field,
                },
            },
        ],
    }


def get_access_token(scope: str) -> str:
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    return credential.get_token(scope).token


def request_with_auth(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any],
) -> requests.Response:
    return requests.request(
        method=method,
        url=url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=json.dumps(payload),
        timeout=60,
    )


def with_api_version(base_url: str, api_version: str) -> str:
    return f"{base_url}?{urlencode({'api-version': api_version})}"


def main() -> int:
    args = parse_args()
    payload = build_payload(args)

    print("Prepared agent payload:")
    print(json.dumps(payload, indent=2))

    if args.dry_run:
        print("Dry run enabled; no request sent.")
        return 0

    token = get_access_token(args.scope)

    if args.agent_id:
        method = "PATCH"
        url = with_api_version(f"{args.agents_base_url.rstrip('/')}/{args.agent_id}", args.api_version)
    else:
        method = "POST"
        url = with_api_version(args.agents_base_url.rstrip("/"), args.api_version)

    response = request_with_auth(method, url, token, payload)
    if not response.ok:
        print("Agent provisioning failed:", file=sys.stderr)
        print(f"HTTP {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1

    body = response.json() if response.content else {}
    print("Agent provisioning succeeded:")
    print(json.dumps(body, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
