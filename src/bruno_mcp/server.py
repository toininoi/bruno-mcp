from __future__ import annotations

from pathlib import Path
import os
import subprocess

from bruno_mcp.executors import CLIExecutor
from bruno_mcp.models import RequestMetadata
from bruno_mcp.parsers import BruParser, EnvParser
from bruno_mcp.scanners import CollectionScanner
from fastmcp import FastMCP


class MCPServer:
    """MCP server for Bruno API collections.

    Provides Model Context Protocol (MCP) resources and tools for discovering
    and executing Bruno API requests. Scans a Bruno collection directory for
    .bru files and exposes them as MCP resources and executable tools.
    """

    def __init__(
        self,
        collection_path: Path,
        executor: CLIExecutor,
        collection_metadata: list[RequestMetadata],
        mcp: FastMCP,
        env_parser: EnvParser,
    ):
        """Initialize MCP server with dependencies.

        Args:
            collection_path: Path to Bruno collection directory.
            executor: CLI executor for HTTP requests.
            collection_metadata: Pre-scanned list of request metadata.
            mcp: FastMCP instance for MCP protocol handling.
            env_parser: Parser for environment files.
        """
        self._collection_path = collection_path
        self._executor = executor
        self._collection_metadata = collection_metadata
        self._mcp = mcp
        self._env_parser = env_parser
        self._register_resources()
        self._register_tools()

    @property
    def mcp(self) -> FastMCP:
        """FastMCP instance for running the server."""
        return self._mcp

    @staticmethod
    def _validate_cli() -> None:
        """Validate that Bruno CLI is available.

        Raises:
            RuntimeError: If CLI validation fails or CLI is not found.
        """
        try:
            result = subprocess.run(
                ["bru", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "Bruno CLI validation failed. Please ensure 'bru' is installed and available in PATH."
                )
        except FileNotFoundError:
            raise RuntimeError(
                "Bruno CLI not found. Please install Bruno CLI and ensure 'bru' is available in PATH."
            )

    @classmethod
    def create(cls) -> "MCPServer":
        """Create MCPServer instance from environment configuration.

        Reads BRUNO_COLLECTION_PATH from environment, scans collection,
        validates CLI availability, and initializes server with CLIExecutor.

        Returns:
            Configured MCPServer instance.

        Raises:
            ValueError: If BRUNO_COLLECTION_PATH environment variable is not set.
            RuntimeError: If Bruno CLI is not available.
        """
        collection_path = os.environ.get("BRUNO_COLLECTION_PATH")
        if not collection_path:
            raise ValueError("BRUNO_COLLECTION_PATH not set")

        cls._validate_cli()

        abs_collection_path = Path(collection_path).resolve()
        bru_parser = BruParser()
        scanner = CollectionScanner(bru_parser)
        collection_metadata = scanner.scan_collection(abs_collection_path)

        return cls(
            collection_path=abs_collection_path,
            executor=CLIExecutor(),
            collection_metadata=collection_metadata,
            mcp=FastMCP("bruno-mcp"),
            env_parser=EnvParser(),
        )

    def _register_resources(self):
        """Register MCP resources with the FastMCP instance."""

        @self._mcp.resource("bruno://collection")
        def collection_tree():
            return [request.model_dump() for request in self._collection_metadata]

        @self._mcp.resource("bruno://environments")
        def environments():
            environments = self._env_parser.list_environments(self._collection_path)
            return [env.model_dump() for env in environments]

    def _register_tools(self):
        """Register MCP tools with the FastMCP instance."""

        @self._mcp.tool()
        def run_request_by_id(
            request_id: str,
            environment_name: str | None = None,
            variable_overrides: dict[str, str] | None = None,
        ):
            """Execute a Bruno request by ID.

            Args:
                request_id: Identifier of the request to execute.
                environment_name: Optional environment name to load variables from.
                variable_overrides: Optional dictionary of variable overrides.

            Returns:
                Dictionary containing the HTTP response (status, headers, body).

            Raises:
                ValueError: If request_id is not found in the collection.
            """
            metadata = next((m for m in self._collection_metadata if m.id == request_id), None)
            if not metadata:
                raise ValueError(f"Request not found: {request_id}")

            request_file_path = Path(metadata.file_path)
            response = self._executor.execute(
                request_file_path,
                self._collection_path,
                environment_name,
                variable_overrides,
            )
            return response.model_dump()

        @self._mcp.tool()
        def list_requests():
            """List all available Bruno requests in the collection.

            Returns a list of all discovered requests with their metadata including
            ID, name, HTTP method, URL (with variable placeholders), and file path.
            This allows MCP clients to discover available endpoints before execution.

            Returns:
                List of dictionaries containing request metadata. Each dictionary includes:
                    - id: Unique identifier (relative path without .bru extension)
                    - name: Human-readable request name
                    - method: HTTP method (GET, POST, PUT, DELETE, etc.)
                    - url: Request URL (may contain {{variable}} placeholders)
                    - file_path: Relative path to the .bru file
            """
            return [request.model_dump() for request in self._collection_metadata]

        @self._mcp.tool()
        def list_environments():
            """List all available environments in the collection.

            Scans the collection's environments directory for .bru files
            and returns a list of environment dictionaries with name and variables.

            Returns:
                List of dictionaries with "name" (str) and "variables" (dict[str, str]) keys.
                Returns empty list if no environments found.
            """
            environments = self._env_parser.list_environments(self._collection_path)
            return [env.model_dump() for env in environments]
