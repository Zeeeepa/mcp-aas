# MCP Tool Crawler Project Notes

## Testing

To run tests:

```bash
poetry run pytest tests/unit/
```

We've added a hook in `conftest.py` to automatically exclude the imported LangGraph node function `test_crawler_code` from being treated as a test function. This prevents pytest from trying to run the imported function as a test.

## Code Conventions

- Node functions in LangGraph should ideally not start with "test_" to avoid confusion with pytest
- When importing functions from modules into test files, be aware of name collisions with pytest's test discovery

## Project Structure

- `src/agents/crawler_generator.py`: Main implementation of the LangGraph-based crawler generator
- `src/models.py`: Data models for crawler components
- `tests/unit/`: Unit tests for the crawler components
- `docs/crawler_generator_architecture.md`: Architecture documentation