"""Tests for MCP server resources and tools."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bruno_mcp import MCPServer
from bruno_mcp.executors import CLIExecutor
from bruno_mcp.models import BruEnvironment, BruResponse, RequestMetadata
from bruno_mcp.parsers import EnvParser


class TestCollectionTreeResource:
    """Test collection_tree MCP resource registration and handler."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance for resource registration tests."""
        return Mock()

    @pytest.fixture
    def mock_executor(self):
        """Mock executor for MCPServer initialization."""
        return Mock()

    @pytest.fixture
    def empty_collection_metadata(self):
        """Empty collection metadata for basic tests."""
        return []

    def test_resource_registered_with_correct_uri(self, mock_mcp, mock_executor, empty_collection_metadata):
        """Test _register_resources calls mcp.resource() with bruno://collection."""
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        mock_mcp.resource.assert_any_call("bruno://collection")

    def test_collection_tree_handler_returns_all_requests(self, mock_mcp, mock_executor):
        """Test collection_tree handler returns all requests from collection_metadata."""
        expected_requests = [
            RequestMetadata(
                id="users/get-user",
                name="Get User",
                method="GET",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/get-user.bru",
            ),
            RequestMetadata(
                id="users/create-user",
                name="Create User",
                method="POST",
                url="https://api.example.com/users",
                file_path="users/create-user.bru",
            ),
        ]

        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=expected_requests,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        resource_decorator = mock_mcp.resource.return_value
        collection_tree_handler = resource_decorator.call_args_list[0][0][0]
        collection_tree = collection_tree_handler()
        assert len(collection_tree) == 2
        assert collection_tree[0]["id"] == "users/get-user"
        assert collection_tree[1]["id"] == "users/create-user"

    def test_collection_tree_handler_includes_complete_metadata(self, mock_mcp, mock_executor):
        """Test collection_tree handler returns all required metadata fields."""
        expected_requests = [
            RequestMetadata(
                id="users/get-user",
                name="Get User",
                method="GET",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/get-user.bru",
            )
        ]
        
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=expected_requests,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        resource_decorator = mock_mcp.resource.return_value
        handler = resource_decorator.call_args_list[0][0][0]
        result = handler()
        request = result[0]
        assert request["id"] == "users/get-user"
        assert request["name"] == "Get User"
        assert request["method"] == "GET"
        assert request["url"] == "https://api.example.com/users/{{userId}}"
        assert request["file_path"] == "users/get-user.bru"


class TestEnvironmentsResource:
    """Test environments MCP resource registration and handler."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance for resource registration tests."""
        return Mock()

    @pytest.fixture
    def mock_executor(self):
        """Mock executor for MCPServer initialization."""
        return Mock()

    @pytest.fixture
    def mock_env_parser(self):
        """Mock EnvParser instance for environment discovery."""
        return Mock()

    @pytest.fixture
    def empty_collection_metadata(self):
        """Empty collection metadata for basic tests."""
        return []

    def test_environments_resource_registered_with_correct_uri(self, mock_mcp, mock_executor, mock_env_parser, empty_collection_metadata):
        """Test _register_resources calls mcp.resource() with bruno://environments."""
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )

        mock_mcp.resource.assert_any_call("bruno://environments")

    def test_environments_resource_handler_returns_all_environments(self, mock_mcp, mock_executor, mock_env_parser, sample_collection_dir):
        """Test handler returns all environments from EnvParser.list_environments()."""
        expected_environments = [
            BruEnvironment(name="local", variables={"baseUrl": "http://localhost:3000", "apiVersion": "v1"}),
            BruEnvironment(name="production", variables={"baseUrl": "https://api.example.com", "apiKey": "{{process.env.API_KEY}}"}),
        ]
        mock_env_parser.list_environments.return_value = expected_environments
        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_executor,
            collection_metadata=[],
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )
        resource_decorator = mock_mcp.resource.return_value
        environments_handler = resource_decorator.call_args_list[1][0][0]

        environments = environments_handler()

        assert len(environments) == 2
        assert environments[0]["name"] == "local"
        assert environments[1]["name"] == "production"
        mock_env_parser.list_environments.assert_called_once_with(sample_collection_dir)

    def test_environments_resource_includes_name_and_variables_with_secrets(self, mock_mcp, mock_executor, mock_env_parser, sample_collection_dir):
        """Test each environment includes name and variables dict with secrets as templates."""
        expected_environments = [
            BruEnvironment(name="local", variables={"baseUrl": "http://localhost:3000", "authToken": "{{process.env.SECRET_TOKEN}}"}),
        ]
        mock_env_parser.list_environments.return_value = expected_environments
        server = MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_executor,
            collection_metadata=[],
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )
        resource_decorator = mock_mcp.resource.return_value
        environments_handler = resource_decorator.call_args_list[1][0][0]

        environments = environments_handler()

        environment = environments[0]
        assert environment["name"] == "local"
        assert "variables" in environment
        assert environment["variables"]["baseUrl"] == "http://localhost:3000"
        assert environment["variables"]["authToken"] == "{{process.env.SECRET_TOKEN}}"


class TestServerCreate:
    """Test MCPServer.create() factory method."""

    @pytest.fixture
    def mock_cli_executor_class(self):
        """Mock CLIExecutor class for create() tests."""
        with patch("bruno_mcp.server.CLIExecutor") as mock:
            yield mock

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess module for CLI validation tests."""
        with patch("bruno_mcp.server.subprocess") as mock:
            yield mock

    @pytest.fixture
    def mock_scanner_class(self):
        """Mock CollectionScanner class for create() tests."""
        with patch("bruno_mcp.server.CollectionScanner") as mock:
            yield mock

    @pytest.fixture
    def mock_parser_class(self):
        """Mock BruParser class for create() tests."""
        with patch("bruno_mcp.server.BruParser") as mock:
            yield mock

    @pytest.fixture
    def mock_fastmcp(self):
        """Mock FastMCP class for create() tests."""
        with patch("bruno_mcp.server.FastMCP") as mock:
            yield mock

    def test_create_scans_collection_and_passes_metadata(
        self,
        mock_cli_executor_class,
        mock_fastmcp,
        mock_scanner_class,
        mock_parser_class,
        mock_subprocess,
        sample_collection_dir,
    ):
        """Test create() scans collection and passes metadata to __init__."""
        mock_parser_instance = mock_parser_class.return_value
        mock_scanner_instance = mock_scanner_class.return_value
        expected_metadata = [
            RequestMetadata(
                id="users/get-user",
                name="Get User",
                method="GET",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/get-user.bru",
            )
        ]
        mock_scanner_instance.scan_collection.return_value = expected_metadata
        mock_subprocess.run.return_value.returncode = 0

        server = MCPServer.create()

        assert server._collection_path.resolve() == sample_collection_dir
        mock_parser_class.assert_called_once()
        mock_scanner_class.assert_called_once_with(mock_parser_instance)
        mock_scanner_instance.scan_collection.assert_called_once_with(sample_collection_dir)
        assert server._collection_metadata == expected_metadata

    def test_create_uses_cli_executor_and_validates_cli(
        self,
        mock_cli_executor_class,
        mock_fastmcp,
        mock_scanner_class,
        mock_subprocess,
    ):
        """Test CLIExecutor used and CLI validated at startup."""
        mock_scanner_instance = mock_scanner_class.return_value
        mock_scanner_instance.scan_collection.return_value = []
        mock_subprocess.run.return_value.returncode = 0

        server = MCPServer.create()

        mock_cli_executor_class.assert_called_once()
        mock_subprocess.run.assert_called_once()
        call_args = mock_subprocess.run.call_args
        assert call_args[0][0] == ["bru", "--version"]

    def test_create_raises_error_when_cli_not_found(
        self, mock_scanner_class, mock_subprocess
    ):
        """Test error when Bruno CLI unavailable."""
        mock_scanner_instance = mock_scanner_class.return_value
        mock_scanner_instance.scan_collection.return_value = []
        mock_subprocess.run.side_effect = FileNotFoundError("bru: command not found")

        with pytest.raises(RuntimeError) as exc_info:
            MCPServer.create()

        assert "Bruno CLI" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_raises_error_without_collection_path(self):
        """Test MCPServer.create() raises error when BRUNO_COLLECTION_PATH not set."""
        with pytest.raises(ValueError, match="BRUNO_COLLECTION_PATH"):
            MCPServer.create()


class TestListRequestsTool:
    """Test list_requests MCP tool registration and handler."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance for tool registration tests."""
        return Mock()

    @pytest.fixture
    def mock_executor(self):
        """Mock executor for MCPServer initialization."""
        return Mock()

    @pytest.fixture
    def empty_collection_metadata(self):
        """Empty collection metadata for basic tests."""
        return []

    def test_list_requests_handler_callable(self, mock_mcp, mock_executor, empty_collection_metadata):
        """Test list_requests handler is registered and callable."""
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        list_requests_handler = all_calls[1][0][0]

        assert mock_mcp.tool.call_count == 3
        assert callable(list_requests_handler)
        assert list_requests_handler.__name__ == "list_requests"

    def test_list_requests_returns_expected_endpoints(self, mock_mcp, mock_executor):
        """Test list_requests returns all requests from collection."""
        expected_requests = [
            RequestMetadata(
                id="users/get-user",
                name="Get User",
                method="GET",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/get-user.bru",
            ),
            RequestMetadata(
                id="posts/create-post",
                name="Create Post",
                method="POST",
                url="https://api.example.com/posts",
                file_path="posts/create-post.bru",
            ),
            RequestMetadata(
                id="posts/list-posts",
                name="List Posts",
                method="GET",
                url="https://api.example.com/posts",
                file_path="posts/list-posts.bru",
            ),
        ]
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=expected_requests,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        handler = tool_decorator.call_args_list[1][0][0]
        result = handler()

        assert len(result) == 3
        assert result[0]["id"] == "users/get-user"
        assert result[1]["id"] == "posts/create-post"
        assert result[2]["id"] == "posts/list-posts"

    def test_list_requests_returns_complete_endpoint_metadata(self, mock_mcp, mock_executor):
        """Test each endpoint includes all required metadata fields."""
        expected_requests = [
            RequestMetadata(
                id="users/delete-user",
                name="Delete User",
                method="DELETE",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/delete-user.bru",
            )
        ]
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=expected_requests,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        handler = tool_decorator.call_args_list[1][0][0]
        result = handler()

        endpoint = result[0]
        assert endpoint["id"] == "users/delete-user"
        assert endpoint["name"] == "Delete User"
        assert endpoint["method"] == "DELETE"
        assert endpoint["url"] == "https://api.example.com/users/{{userId}}"
        assert endpoint["file_path"] == "users/delete-user.bru"
        assert "{{userId}}" in endpoint["url"]

    def test_list_requests_handles_empty_collection(self, mock_mcp, mock_executor, empty_collection_metadata):
        """Test list_requests returns empty list when collection is empty."""
        MCPServer(
            collection_path=Path("/empty"),
            executor=mock_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        handler = tool_decorator.call_args[0][0]
        result = handler()

        assert result == []
        assert isinstance(result, list)


class TestRunBrunoRequestTool:
    """Test run_bruno_request MCP tool registration and handler."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance for tool registration tests."""
        return Mock()

    @pytest.fixture
    def mock_cli_executor(self):
        """Mock CLIExecutor instance for execution tests."""
        return Mock(spec=CLIExecutor)

    @pytest.fixture
    def empty_collection_metadata(self):
        """Empty collection metadata for basic tests."""
        return []

    @pytest.fixture
    def sample_collection_metadata(self):
        """Sample collection metadata with one request."""
        return [
            RequestMetadata(
                id="users/get-user",
                name="Get User",
                method="GET",
                url="https://api.example.com/users/{{userId}}",
                file_path="users/get-user.bru",
            )
        ]

    def test_run_request_by_id_tool_registered(self, mock_mcp, mock_cli_executor, empty_collection_metadata):
        """Test run_request_by_id tool is registered with correct name."""
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_cli_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        run_request_handler = all_calls[0][0][0]

        assert run_request_handler.__name__ == "run_request_by_id"

    def test_tool_passes_file_path_to_executor(
        self, sample_collection_dir, mock_cli_executor, mock_mcp, sample_collection_metadata
    ):
        """Test file path passed correctly to executor."""
        mock_cli_executor.execute.return_value = BruResponse(
            status=200,
            headers={},
            body="",
        )

        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_cli_executor,
            collection_metadata=sample_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        handler = all_calls[0][0][0]
        handler(request_id="users/get-user")

        mock_cli_executor.execute.assert_called_once()
        call_args = mock_cli_executor.execute.call_args
        assert call_args[0][0] == Path("users/get-user.bru")
        assert call_args[0][1] == sample_collection_dir

    def test_tool_returns_executor_response(
        self, sample_collection_dir, mock_cli_executor, mock_mcp, sample_collection_metadata
    ):
        """Test handler returns executor response correctly."""
        expected_response = BruResponse(
            status=200,
            headers={"Content-Type": "application/json"},
            body='{"id": "123", "name": "John"}',
        )
        mock_cli_executor.execute.return_value = expected_response

        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_cli_executor,
            collection_metadata=sample_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        handler = all_calls[0][0][0]
        result = handler(request_id="users/get-user")

        assert result["status"] == 200
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["body"] == '{"id": "123", "name": "John"}'

    def test_tool_passes_environment_name_to_executor(
        self, sample_collection_dir, mock_cli_executor, mock_mcp, sample_collection_metadata
    ):
        """Test environment_name passed correctly to executor."""
        mock_cli_executor.execute.return_value = BruResponse(
            status=200,
            headers={},
            body='{"id": "456"}',
        )
        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_cli_executor,
            collection_metadata=sample_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        handler = all_calls[0][0][0]
        result = handler(request_id="users/get-user", environment_name="local")

        assert result["status"] == 200
        mock_cli_executor.execute.assert_called_once()
        call_args = mock_cli_executor.execute.call_args
        assert call_args[0][2] == "local"

    def test_tool_passes_variable_overrides_to_executor(
        self, sample_collection_dir, mock_cli_executor, mock_mcp, sample_collection_metadata
    ):
        """Test variable_overrides passed correctly to executor."""
        mock_cli_executor.execute.return_value = BruResponse(
            status=200,
            headers={},
            body='{"id": "456"}',
        )
        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_cli_executor,
            collection_metadata=sample_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        handler = all_calls[0][0][0]
        result = handler(request_id="users/get-user", variable_overrides={"userId": "456"})

        assert result["status"] == 200
        mock_cli_executor.execute.assert_called_once()
        call_args = mock_cli_executor.execute.call_args
        assert call_args[0][3] == {"userId": "456"}

    def test_tool_raises_error_for_invalid_request_id(
        self, sample_collection_dir, mock_cli_executor, mock_mcp, sample_collection_metadata
    ):
        """Test error handling when request_id not found."""
        MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_cli_executor,
            collection_metadata=sample_collection_metadata,
            mcp=mock_mcp,
            env_parser=EnvParser(),
        )

        tool_decorator = mock_mcp.tool.return_value
        all_calls = tool_decorator.call_args_list
        handler = all_calls[0][0][0]

        with pytest.raises(ValueError, match="Request not found"):
            handler(request_id="users/nonexistent")


class TestListEnvironmentsTool:
    """Test list_environments MCP tool registration and handler."""

    @pytest.fixture
    def mock_mcp(self):
        """Mock FastMCP instance for tool registration tests."""
        return Mock()

    @pytest.fixture
    def mock_executor(self):
        """Mock executor for MCPServer initialization."""
        return Mock()

    @pytest.fixture
    def mock_env_parser(self):
        """Mock EnvParser instance for environment discovery."""
        return Mock()

    @pytest.fixture
    def empty_collection_metadata(self):
        """Empty collection metadata for basic tests."""
        return []

    def test_list_environments_tool_registered_and_callable(self, mock_mcp, mock_executor, mock_env_parser, empty_collection_metadata):
        """Test list_environments tool is registered and callable."""
        MCPServer(
            collection_path=Path("/test"),
            executor=mock_executor,
            collection_metadata=empty_collection_metadata,
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )
        tool_decorator = mock_mcp.tool.return_value
        list_environments_handler = tool_decorator.call_args_list[2][0][0]

        assert callable(list_environments_handler)
        assert list_environments_handler.__name__ == "list_environments"

    def test_list_environments_returns_parsed_environment_list(self, mock_mcp, mock_executor, mock_env_parser, sample_collection_dir):
        """Test tool returns environments from EnvParser.list_environments()."""
        expected_environments = [
            BruEnvironment(name="local", variables={"baseUrl": "http://localhost:3000", "apiVersion": "v1"}),
            BruEnvironment(name="production", variables={"baseUrl": "https://api.example.com", "apiKey": "{{process.env.API_KEY}}"}),
        ]
        mock_env_parser.list_environments.return_value = expected_environments
        server = MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_executor,
            collection_metadata=[],
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )
        tool_decorator = mock_mcp.tool.return_value
        list_environments_handler = tool_decorator.call_args_list[2][0][0]

        result = list_environments_handler()

        assert len(result) == 2
        assert result[0]["name"] == "local"
        assert result[0]["variables"]["baseUrl"] == "http://localhost:3000"
        assert result[1]["name"] == "production"
        assert result[1]["variables"]["apiKey"] == "{{process.env.API_KEY}}"
        mock_env_parser.list_environments.assert_called_once_with(sample_collection_dir)

    def test_list_environments_handles_empty_environments_directory(self, mock_mcp, mock_executor, mock_env_parser, sample_collection_dir):
        """Test tool returns empty list when no environments found."""
        mock_env_parser.list_environments.return_value = []
        server = MCPServer(
            collection_path=sample_collection_dir,
            executor=mock_executor,
            collection_metadata=[],
            mcp=mock_mcp,
            env_parser=mock_env_parser,
        )
        tool_decorator = mock_mcp.tool.return_value
        list_environments_handler = tool_decorator.call_args_list[2][0][0]

        result = list_environments_handler()

        assert result == []

