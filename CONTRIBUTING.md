# Contributing to Sherly AI

Thank you for contributing to Sherly AI! We welcome bug fixes, documentation improvements, and capability plugins.

---

## 1. Development Workflow

1. **Fork & Branch**:
   ```bash
   git checkout -b fix/issue-description
   ```
2. **Set Up Development Environment**:
   Follow [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md).
3. **Coding Standards**:
   - Python: Type annotations, clean docstrings, snake_case.
   - Frontend: TypeScript, React hooks, Tailwind CSS classes.
4. **Run Test Suite**:
   ```bash
   pytest tests/ -q
   ```
5. **Submit Pull Request**:
   Describe your changes clearly with relevant issue references.

---

## 2. Commit Message Guidelines

We follow Conventional Commits:
- `feat:` New features or capabilities
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Unit or integration test additions
- `refactor:` Code improvements with zero behavior change
