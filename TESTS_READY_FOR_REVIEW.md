# BruParser Tests - Ready for Review

## Summary

I've created a comprehensive test suite for the Bruno .bru file parser. The tests are written following TDD principles and define the expected behavior before implementation.

## What Has Been Created

### 1. Test Files
- **tests/test_parser.py** (612 lines, 42 test functions, 14 test classes)
- **tests/conftest.py** - Pytest fixtures for test directories
- **tests/__init__.py** - Test package marker

### 2. Test Fixtures (11 .bru files)

**Valid Requests** (8 files in `tests/fixtures/sample_collection/`):
- `users/get-user.bru` - Simple GET with query params and headers
- `users/create-user.bru` - POST with JSON body
- `users/update-user.bru` - PUT with JSON body and auth section
- `users/delete-user.bru` - DELETE request (minimal structure)
- `posts/list-posts.bru` - GET with template variables
- `posts/create-post.bru` - POST with multiple headers
- `posts/form-data.bru` - POST with form-urlencoded body
- `posts/form-upload.bru` - POST with multipart-form body

**Invalid Files** (3 files in `tests/fixtures/invalid/`):
- `malformed-braces.bru` - Missing closing brace (error test)
- `missing-method.bru` - No HTTP method defined (error test)
- `empty-file.bru` - Empty file (error test)

### 3. Project Structure Files
- **pyproject.toml** - Project configuration with dependencies
- **src/bruno_mcp/parsers/bru_parser.py** - Stub file with Pydantic models and NotImplementedError placeholders
- **src/bruno_mcp/__init__.py** - Package marker
- **src/bruno_mcp/parsers/__init__.py** - Parser package with exports

### 4. Documentation
- **TEST_SUMMARY.md** - Detailed test documentation
- **TESTS_READY_FOR_REVIEW.md** - This file

## Test Organization

The tests are organized into 14 test classes:

1. **TestBruRequestModel** (5 tests) - Pydantic model behavior
2. **TestBruParserSimpleGET** (3 tests) - Basic GET request parsing
3. **TestBruParserPOSTWithBody** (3 tests) - POST with different body types
4. **TestBruParserPUTRequests** (1 test) - PUT request with auth
5. **TestBruParserHeadersAndParams** (3 tests) - Headers and query parameters
6. **TestBruParserMetadata** (2 tests) - Meta section parsing
7. **TestBruParserErrorHandling** (4 tests) - Error cases and exceptions
8. **TestBruParserRequestID** (2 tests) - Request ID generation
9. **TestBruParserEdgeCases** (4 tests) - Edge cases and state isolation
10. **TestBruParserAuthSection** (2 tests) - Authentication sections
11. **TestBruParserBodyTypes** (2 tests) - Body content type detection
12. **TestBruParserHTTPMethods** (5 tests) - HTTP method parsing
13. **TestBruParserURLParsing** (3 tests) - URL extraction
14. **TestBruParserIntegration** (3 tests) - Full integration scenarios

## Key Test Scenarios Covered

### ✅ Happy Path
- All HTTP methods (GET, POST, PUT, DELETE)
- Query parameters and headers parsing
- Multiple body types (JSON, form-urlencoded, multipart-form)
- Authentication sections (bearer tokens)
- Template variables ({{userId}}, {{baseUrl}})
- Metadata extraction (name, type, seq)

### ✅ Error Handling
- Malformed files (missing braces)
- Missing required sections (no HTTP method)
- Empty files
- Non-existent files (FileNotFoundError)

### ✅ Edge Cases
- Requests without optional sections (headers, params, body, auth)
- Multiple files parsed sequentially
- Parser state isolation between calls
- Headers/values containing colons
- URLs starting with variables

### ✅ Data Validation
- HTTP methods normalized to uppercase
- Meta seq field parsed as integer
- Body content preserved as string
- Request ID generated from filepath

## Current Status

- ✅ **612 lines of test code written**
- ✅ **42 test functions defined**
- ✅ **11 .bru fixture files created**
- ✅ **Test fixtures cover all major scenarios**
- ⏳ **Stub implementation in place (NotImplementedError)**
- ⏳ **Ready for implementation to begin**

## Test Philosophy

The tests follow these principles:

1. **Test-Driven Development (TDD)**
   - Tests written before implementation
   - Tests define the expected behavior
   - Implementation will be guided by test requirements

2. **Comprehensive Coverage**
   - Happy paths and error cases
   - Edge cases and boundary conditions
   - Integration scenarios

3. **Clear Assertions**
   - Each test has explicit assertions
   - Test names clearly describe what's being tested
   - Docstrings explain the purpose

4. **Isolated Tests**
   - Each test is independent
   - No shared state between tests
   - Can run in any order

5. **Realistic Fixtures**
   - Test data mirrors real Bruno .bru files
   - Covers various real-world scenarios
   - Includes both valid and invalid cases

## How to Run Tests (Once Implementation is Done)

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/test_parser.py -v

# Run with coverage
pytest tests/test_parser.py --cov=bruno_mcp.parsers.bru_parser --cov-report=term-missing

# Run specific test class
pytest tests/test_parser.py::TestBruParserSimpleGET -v
```

## Expected Implementation Approach

Based on the tests, the parser should:

1. **Read file content** line by line
2. **Use state machine** to track current section
3. **Split into sections** when encountering `section_name {`
4. **Parse each section** based on its type:
   - `meta {}` → Parse as key-value pairs, convert seq to int
   - `get/post/put/delete {}` → Extract URL, normalize method to uppercase
   - `params:query {}` → Parse as key-value dict
   - `headers {}` → Parse as key-value dict (handle colons in values)
   - `body:json/form-urlencoded/multipart-form {}` → Capture type and content
   - `auth:bearer/basic {}` → Parse auth type and credentials
5. **Return BruRequest** Pydantic model with all parsed data

## Review Checklist

Please review the following:

- [ ] Test coverage is comprehensive
- [ ] Test fixtures represent real-world scenarios
- [ ] Error test cases are appropriate
- [ ] Test organization makes sense
- [ ] Test names are clear and descriptive
- [ ] Assertions are specific and meaningful
- [ ] Any missing test scenarios?
- [ ] Any changes needed to fixtures?
- [ ] Ready to proceed with implementation?

## Next Steps After Review

Once you approve the tests:

1. Implement `BruParser._split_into_sections()` method
2. Implement `BruParser._parse_meta()` method
3. Implement `BruParser._parse_method_and_url()` method
4. Implement `BruParser._parse_key_value_section()` method
5. Implement `BruParser._parse_body()` method
6. Implement `BruParser.parse_file()` method (orchestrates all parsing)
7. Implement `BruRequest.get_request_id()` method
8. Run tests iteratively and fix issues
9. Achieve target coverage (>90%)

## Questions for Review

1. Are there any .bru file formats or scenarios I haven't covered?
2. Should I add more edge case tests?
3. Do the test fixtures accurately represent Bruno's .bru format?
4. Any specific error messages or exception types you'd prefer?
5. Should the parser be more lenient or strict with malformed files?

---

**Status**: ✅ Ready for your review
**Next**: Awaiting feedback before implementation begins
