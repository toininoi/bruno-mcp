# Test Suite for BruParser

## Overview

Focused, MVP-appropriate test suite for the Bruno .bru file parser. Tests follow the AAA (Arrange, Act, Assert) pattern with 2-3 assertions per test.

## Test Structure

```
tests/
├── conftest.py                      # Pytest fixtures
├── test_parser.py                   # Parser tests (292 lines, 19 tests)
└── fixtures/
    ├── sample_collection/           # Valid .bru test files
    │   ├── users/
    │   │   ├── get-user.bru        # GET with params & headers
    │   │   ├── create-user.bru     # POST with JSON body
    │   │   ├── update-user.bru     # PUT with JSON & auth
    │   │   └── delete-user.bru     # DELETE request
    │   └── posts/
    │       ├── list-posts.bru      # GET with variables
    │       ├── create-post.bru     # POST with headers
    │       ├── form-data.bru       # Form-urlencoded body
    │       └── form-upload.bru     # Multipart-form body
    └── invalid/                     # Malformed files
        ├── malformed-braces.bru     # Missing closing brace
        └── empty-file.bru           # Empty file
```

## Test Coverage (19 tests)

### 1. Model Tests (2 tests) - TestBruRequestModel
- ✓ get_name() returns name from meta
- ✓ get_name() returns default when missing

### 2. GET Requests (3 tests) - TestBruParserGETRequests
- ✓ Parse simple GET request
- ✓ Parse query parameters
- ✓ Parse headers

### 3. POST Requests (2 tests) - TestBruParserPOSTRequests
- ✓ Parse POST with JSON body
- ✓ Parse POST with form-urlencoded body

### 4. Other HTTP Methods (2 tests) - TestBruParserOtherMethods
- ✓ Parse PUT request
- ✓ Parse DELETE request

### 5. Metadata (2 tests) - TestBruParserMetadata
- ✓ Parse meta section (name, type, seq)
- ✓ Verify seq is parsed as integer

### 6. Authentication (1 test) - TestBruParserAuth
- ✓ Parse bearer token authentication

### 7. URL Parsing (2 tests) - TestBruParserURLs
- ✓ Parse URLs with template variables
- ✓ Parse full URLs with protocol

### 8. Error Handling (2 tests) - TestBruParserErrorHandling
- ✓ Raise error for unmatched braces
- ✓ Raise FileNotFoundError for missing file

### 9. Integration (3 tests) - TestBruParserIntegration
- ✓ Parse complete request with all sections
- ✓ Parse minimal request
- ✓ Handle multiple files sequentially

## Test Principles

### AAA Pattern
Every test follows the Arrange-Act-Assert structure:
```python
def test_example(self, sample_collection_dir):
    # Arrange
    parser = BruParser()
    filepath = sample_collection_dir / "users" / "get-user.bru"

    # Act
    request = parser.parse_file(str(filepath))

    # Assert
    assert request.method == "GET"
    assert request.url == "https://api.example.com/users/{{userId}}"
```

### Focused Assertions
- 2-3 assertions per test maximum
- No redundant existence checks (e.g., `assert "key" in dict`)
- Direct value assertions only

### MVP-Appropriate
- Only critical error handling (malformed files, missing files)
- No over-testing of edge cases
- No duplication across test classes

## Running the Tests

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/test_parser.py -v

# Run specific test class
pytest tests/test_parser.py::TestBruParserGETRequests -v

# Run with coverage
pytest tests/test_parser.py --cov=bruno_mcp.parsers.bru_parser
```

## Implementation Checklist

The parser must:
- [ ] Parse all HTTP methods (GET, POST, PUT, DELETE)
- [ ] Extract meta section (name, type, seq as int)
- [ ] Parse query parameters as dict
- [ ] Parse headers as dict
- [ ] Detect body type (json, form-urlencoded, multipart-form)
- [ ] Capture body content as string
- [ ] Parse auth section (type, token)
- [ ] Preserve template variables like {{userId}}
- [ ] Raise exception for malformed files
- [ ] Raise FileNotFoundError for missing files
- [ ] Handle multiple sequential parses without state leakage

## Key Test Files to Review

1. **test_parse_simple_get_request** - Foundation test
2. **test_parse_post_with_json_body** - Body parsing
3. **test_parse_file_with_missing_closing_brace** - Error handling
4. **test_parse_complete_request_with_all_sections** - Integration
5. **test_parser_handles_multiple_files** - State isolation
