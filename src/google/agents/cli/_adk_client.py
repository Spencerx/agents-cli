# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared ADK FastAPI HTTP client: session create + ``/run_sse`` stream."""

from __future__ import annotations

import json
from collections.abc import Iterator

import click
import requests

_SESSION_TIMEOUT = 30
_RUN_SSE_TIMEOUT = 120


def create_session(
    base_url: str,
    app_name: str,
    user_id: str,
    *,
    headers: dict,
) -> str:
    """Create an ADK session and return its ID."""
    session_url = f"{base_url}/apps/{app_name}/users/{user_id}/sessions"
    resp = requests.post(session_url, headers=headers, json={}, timeout=_SESSION_TIMEOUT)
    if not resp.ok:
        hint = ""
        if resp.status_code in (404, 405):
            hint = "\n  If this is an A2A agent, try --mode a2a instead."
        raise click.ClickException(
            f"Failed to create session (HTTP {resp.status_code}):\n  {resp.text}{hint}"
        )
    return resp.json().get("id")


def run_sse(
    base_url: str,
    app_name: str,
    session_id: str,
    *,
    user_message: dict,
    headers: dict,
    user_id: str,
) -> Iterator[dict]:
    """Stream ADK events for a single user turn.

    Yields each ``data:`` line's decoded JSON dict as it arrives. Blank
    lines, non-``data:`` lines, and payloads that fail to JSON-decode are
    silently skipped.
    """
    run_url = f"{base_url}/run_sse"
    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": user_message,
    }

    with requests.post(
        run_url, headers=headers, json=payload, stream=True, timeout=_RUN_SSE_TIMEOUT
    ) as resp:
        if not resp.ok:
            raise click.ClickException(
                f"Failed to run agent (HTTP {resp.status_code}):\n  {resp.text}"
            )
        for line in resp.iter_lines(decode_unicode=True):
            if not isinstance(line, str) or not line.startswith("data: "):
                continue
            data_str = line[len("data: ") :]
            try:
                yield json.loads(data_str)
            except json.JSONDecodeError:
                continue
