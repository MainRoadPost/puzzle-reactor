"""
Patched Puzzle client with cookie-based authentication and WebSocket support.

This module extends the auto-generated puzzle.Client without modifying the generated code.
It provides:
- Cookie-based authentication support for HTTP and WebSocket connections
- WebSocket compatibility with websockets 15.x library
"""

# pyright: reportUnknownMemberType=false

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import httpx

from puzzle.async_base_client import GRAPHQL_TRANSPORT_WS, GraphQLTransportWSMessageType
from puzzle.client import Client

try:
    from websockets import connect as ws_connect
    from websockets.typing import Subprotocol
except ImportError:
    raise ImportError(
        "Subscriptions require 'websockets' package. Install with: pip install websockets"
    )


class PuzzleClient(Client):
    """
    Enhanced Puzzle client with cookie-based authentication.

    Extends the auto-generated Client class to:
    - Enable cookie persistence for authentication
    - Extract cookies from HTTP client and pass them to WebSocket connections
    - Use websockets 15.x compatible API
    """

    def __init__(
        self,
        url: str = "",
        headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
        ws_url: str = "",
        ws_headers: dict[str, Any] | None = None,
        ws_origin: str | None = None,
        ws_connection_init_payload: dict[str, Any] | None = None,
    ) -> None:
        # Initialize with a custom http_client that has cookie support if not provided
        if http_client is None:
            http_client = httpx.AsyncClient(
                headers=headers,
                cookies=httpx.Cookies(),  # Enable cookie jar
            )

        # Call parent constructor
        super().__init__(
            url=url,
            headers=headers,
            http_client=http_client,
            ws_url=ws_url,
            ws_headers=ws_headers,
            ws_origin=ws_origin,
            ws_connection_init_payload=ws_connection_init_payload,
        )

    async def execute_ws(
        self,
        query: str,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Execute a GraphQL subscription over WebSocket with cookie authentication.

        This method overrides the parent's execute_ws to:
        1. Extract cookies from the HTTP client session
        2. Include cookies in the WebSocket connection headers
        3. Use 'additional_headers' parameter for websockets 15.x compatibility
        """
        headers = self.ws_headers.copy()
        headers.update(kwargs.get("extra_headers", {}))

        # Extract cookies from HTTP client and add to WebSocket headers
        if self.http_client.cookies:
            cookie_header = "; ".join(
                [
                    f"{cookie.name}={cookie.value}"
                    for cookie in self.http_client.cookies.jar
                ]
            )
            if cookie_header:
                headers["Cookie"] = cookie_header

        # Build kwargs for websockets 15.x
        # Use 'additional_headers' instead of 'extra_headers' for websockets 15.x
        merged_kwargs: dict[str, Any] = {}

        if self.ws_origin:
            merged_kwargs["origin"] = self.ws_origin

        if headers:
            merged_kwargs["additional_headers"] = headers

        # Pass through any other kwargs except extra_headers (already processed)
        for key, value in kwargs.items():
            if key != "extra_headers":
                merged_kwargs[key] = value

        # Execute the WebSocket subscription
        operation_id = str(uuid4())
        async with ws_connect(
            self.ws_url,
            subprotocols=[Subprotocol(GRAPHQL_TRANSPORT_WS)],
            **merged_kwargs,
        ) as websocket:
            # Initialize connection
            await self._send_connection_init(websocket)

            # Wait for connection acknowledgment
            await self._handle_ws_message(
                await websocket.recv(),
                websocket,
                expected_type=GraphQLTransportWSMessageType.CONNECTION_ACK,
            )

            # Subscribe to the operation
            await self._send_subscribe(
                websocket,
                operation_id=operation_id,
                query=query,
                operation_name=operation_name,
                variables=variables,
            )

            # Yield messages as they arrive
            async for message in websocket:
                data = await self._handle_ws_message(message, websocket)
                if data:
                    yield data
