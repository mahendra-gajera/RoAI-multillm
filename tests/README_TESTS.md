# Unit Tests

## Overview

This directory contains unit tests for the RoAI Multi-LLM Platform core functionality.

## Test Coverage

### ✅ Test Files (23 tests total)

1. **`test_router.py`** (9 tests) - Intelligent routing logic
   - Strict JSON routing to OpenAI
   - Long context routing to Gemini
   - Multi-document routing to Gemini
   - High impact routing to Ensemble
   - Default routing to OpenAI
   - Priority rule testing
   - Routing explanations
   - Edge case/boundary testing

2. **`test_cost_calculator.py`** (8 tests) - Cost tracking and calculation
   - OpenAI cost calculation (GPT-4o, GPT-4o-mini)
   - Gemini cost calculation (Flash)
   - Model cost comparisons
   - Zero token edge cases
   - Session cost tracking
   - Cost breakdown by provider

3. **`test_roai_calculator.py`** (7 tests) - RoAI metrics
   - Positive ROI calculations
   - Zero LLM cost handling
   - Negative ROI scenarios
   - Break-even calculations
   - High fraud prevention value
   - Metadata validation
   - Scenario comparisons

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_router.py -v
pytest tests/test_cost_calculator.py -v
pytest tests/test_roai_calculator.py -v
```

### Run Specific Test
```bash
pytest tests/test_router.py::TestLLMRouter::test_router_strict_json_routes_to_openai -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to view report
```

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
collected 23 items

tests/test_cost_calculator.py ........                                  [ 34%]
tests/test_roai_calculator.py .......                                   [ 65%]
tests/test_router.py ........                                           [100%]

======================== 23 passed, 1 warning in 0.12s ========================
```

## Test Configuration

- **pytest.ini**: Test discovery and reporting configuration
- **conftest.py**: Shared fixtures and path setup
- **fixtures**: Using pytest fixtures for test isolation

## Adding New Tests

To add new tests:

1. Create test file: `tests/test_<module_name>.py`
2. Import module to test
3. Create test class: `class Test<ModuleName>:`
4. Add test methods: `def test_<scenario>(self, fixtures):`
5. Use assertions to verify behavior

Example:
```python
import pytest
from app.module import MyClass

class TestMyClass:
    @pytest.fixture
    def instance(self):
        return MyClass()

    def test_basic_functionality(self, instance):
        result = instance.do_something()
        assert result == expected_value
```

## Best Practices

✅ **DO:**
- Write descriptive test names
- Test edge cases and boundaries
- Use fixtures for setup/teardown
- Keep tests isolated and independent
- Assert specific values, not just truthiness

❌ **DON'T:**
- Test implementation details
- Write tests that depend on order
- Use real API calls (mock instead)
- Ignore failing tests
- Write overly complex tests

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=app
```

## Future Test Additions

Potential areas for expansion:
- Integration tests for full workflow
- Mock API response testing
- Ensemble validation logic
- Observability service tests
- Admin dashboard functionality tests
