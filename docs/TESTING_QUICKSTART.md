# Testing Quick Reference

**Quick access to testing documentation and common commands.**

---

## Quick Stats

- **Total Tests:** 1,113 (99.6% passing)
- **Coverage:** 66.0%
- **Test Files:** 36
- **Execution Time:** ~10 seconds

---

## Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Run specific module
pytest tests/unit/test_agent_state.py -v

# Run failed tests only
pytest tests/ --lf

# Run tests matching pattern
pytest tests/ -k "session" -v

# Stop on first failure
pytest tests/ -x
```

---

## Test Structure

```
tests/
├── unit/              # 31 files, ~819 tests - Unit tests
├── test_sessions/     # 4 files, 53 tests - Session Manager (P8)
├── integration/       # 1 file, ~241 tests - Integration tests
└── fixtures/          # Test fixtures and mocks
```

---

## Coverage Targets

| Priority | Target | Current |
|----------|--------|---------|
| Overall | >65% | 66.0% ✅ |
| Critical modules | >80% | 85%+ ✅ |
| New features | >70% | Enforce in PR |

---

## Writing Tests

### Test Template

```python
import pytest

class TestMyFeature:
    def test_basic_behavior(self):
        # Arrange
        obj = MyClass()

        # Act
        result = obj.method()

        # Assert
        assert result.success

    async def test_async_behavior(self):
        # Use async/await for async functions
        result = await async_method()
        assert result is not None
```

### Best Practices

1. ✅ Test one thing per test
2. ✅ Use descriptive names
3. ✅ Follow Arrange-Act-Assert
4. ✅ Use fixtures for setup
5. ❌ Don't test implementation details
6. ❌ Don't write interdependent tests

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest tests/ --cov=src --cov-report=xml

- name: Check coverage
  run: coverage report --fail-under=65
```

---

## Full Documentation

📖 **[Complete Test Quality Report](./TEST_QUALITY_REPORT.md)**

Detailed analysis including:
- Module-by-module coverage breakdown
- Test category deep dives
- Recommendations for improvement
- Testing best practices
- CI/CD integration guide

---

**Last Updated:** 2025-11-17
