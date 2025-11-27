#!/usr/bin/env python3
"""
Example reactor application for interacting with the Puzzle API.

Demonstrates:
- Authentication via GraphQL
- Executing GraphQL queries (retrieving a list of projects)
- WebSocket subscriptions for tracking real-time changes
"""

import asyncio
import os
import logging

from dotenv import load_dotenv

# Import the patched Puzzle client and related classes
# The patch adds WebSocket subscription support to the base ariadne-codegen client
from puzzle_client_patched import PuzzleClient
from puzzle.exceptions import GraphQLClientHttpError
from puzzle.get_projects import GetProjectsProjects

# Configure logging to emit informational messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


class PuzzleReactor:
    """Handles interactions with the Puzzle API to react to events.

    The class handles:
    - Puzzle authentication via GraphQL
    - Retrieving a list of active projects via GraphQL queries
    - Monitoring changes to projects and products via WebSocket subscriptions
    """

    def __init__(self):
        """Initializes the Puzzle client with both HTTP and WebSocket connections."""
        load_dotenv()  # Load environment variables from the .env file

        PUZZLE_API = os.getenv("PUZZLE_API")
        if not PUZZLE_API:
            raise ValueError("PUZZLE_API environment variable is not set.")

        # Convert the HTTP URL to a WebSocket URL (http -> ws, /api/graphql -> /api/graphql/ws)
        ws_url = PUZZLE_API.replace("http", "ws").replace(
            "/api/graphql", "/api/graphql/ws"
        )

        # Create a client that supports both HTTP requests and WebSocket subscriptions
        self.client = PuzzleClient(url=PUZZLE_API, ws_url=ws_url)

    async def login(self):
        """Authenticates against the Puzzle API using a GraphQL mutation.

        Returns:
            bool: True if authentication succeeded, False otherwise.
        """
        domain = os.getenv("PUZZLE_USER_DOMAIN")
        username = os.getenv("PUZZLE_USERNAME")
        password = os.getenv("PUZZLE_PASSWORD")

        # Check that required credentials are present
        if username is None or password is None:
            logging.error("Login failed: Missing credentials.")
            return False

        try:
            response = await self.client.login(
                domain_name=domain if domain and len(domain) > 0 else None,
                username=username,
                password=password,
            )

            if response.login:
                # After successful authentication the cookie will be saved
                # to http_client.cookies and used for subsequent
                # HTTP requests and WebSocket connections
                logging.info("Login successful.")
                return True
            else:
                logging.error("Login failed.")
                return False
        except GraphQLClientHttpError as e:
            logging.error(f"Login failed: {e.response}")
            return False

    async def fetch_projects(self) -> list[GetProjectsProjects]:
        """Fetches active projects using a GraphQL query.

        Returns:
            list[GetProjectsProjects]: A list of active projects (where done_at is None).
        """
        try:
            response = await self.client.get_projects()
            if response.projects:
                # Filter only active projects (with done_at == None)
                # These are projects that are not yet finished
                active_projects = [p for p in response.projects if p.done_at is None]

                return active_projects
            else:
                logging.error("Failed to fetch projects.")
                return []
        except GraphQLClientHttpError as e:
            logging.error(f"Error fetching projects: {e.response}")
            return []

    async def run(self):
        """Runs the application's main process.

        Authenticates first, then creates WebSocket subscriptions to monitor
        real-time project and product updates.
        """
        # First authenticate
        if not await self.login():
            return

        # Optional example: fetch the list of active projects
        # active_projects = await self.fetch_projects()
        # if not active_projects:
        #     return
        #
        # # Process fetched projects
        # for project in active_projects:
        #     logging.info(f"Processing project: {project.title}")

        # Create handlers for WebSocket subscriptions
        async def handle_projects():
            """Handle project update events coming through the WebSocket."""
            async for projectUpdated in self.client.on_projects_updated():
                logging.info(f"Project updated: {projectUpdated}")

        async def handle_products():
            """Handle product update events coming through the WebSocket."""
            async for productsUpdated in self.client.on_products_updated():
                logging.info(f"Products updated: {productsUpdated}")

        # Run both subscriptions in parallel
        # Both will listen concurrently and react to real-time events
        await asyncio.gather(handle_projects(), handle_products())


if __name__ == "__main__":
    app = PuzzleReactor()
    asyncio.run(app.run())
