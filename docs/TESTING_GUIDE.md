# Testing Guide

Sherly relies on a comprehensive test suite to ensure the deterministic safety layers, parsing logic, and state management remain intact. We currently have over 210 passing tests.

## 🏃 Running Tests

We use `pytest` as our testing framework. 

To run the entire test suite:
```bash
pytest tests/
```

To run a specific test file:
```bash
pytest tests/test_command_router.py
```

## 🎯 Test Strategy

1. **Unit Tests (Core Logic):**
   - The majority of our tests focus on `sherly_core` and `safety_guard`. 
   - We mock out the LLM responses to ensure tests run quickly and deterministically without requiring a local GPU.
   
2. **Integration Tests:**
   - We test the flow from `input_validator` -> `command_router` -> `action_manager`.
   - These tests ensure that when an action is flagged as `CONFIRM`, it is properly staged in memory and *not* written to disk automatically.

3. **UI Tests:**
   - PySide6 UI tests verify that the patching window opens correctly and handles `approve`/`reject` signals accurately.

## 🚧 Edge Cases Handled

- **Malformed Diff Generation:** LLMs frequently generate malformed markdown diffs. Our test suite includes dozens of examples of hallucinated or badly formatted diffs to ensure `action_manager.py` fails gracefully rather than corrupting user files.
- **Prompt Injection:** We test against known jailbreak strings to ensure `safety_guard.py` triggers an immediate block.
- **Concurrent Requests:** Tests simulate rapid-fire inputs to ensure the locking mechanisms prevent race conditions.

## 🔮 Future Automation

- **GitHub Actions:** We plan to integrate `pytest` into a CI pipeline for every PR.
- **Mocked Ollama Server:** A lightweight mock server to simulate slow LLM responses and test the timeout/circuit-breaker logic under load.
