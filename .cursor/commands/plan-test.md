I want you to give some more fine-grained detail for the tests for the part of the codebase I want you to write tests for.

The details I want are:
- The fixtures you intend to create for each class block.
- The tests blocks you plan to organise tests under
- The name of each test
- The purpose of each test (max 5-10 words)

There also some style guides the tests should comply with:
- Three unified, separate Arrange, Act and Assert blocks. Think of each block as a paragraph. Don't comment above which block is which.
- Each test file should be in a folder. If no appropriate folder for this exists, then a new folder can be created. The test folder and application code folder names should match.
- Fixtures which aren't directly accessed in any test within the block should have a comment explaining their purpose.