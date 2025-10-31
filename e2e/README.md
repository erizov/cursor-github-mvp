# e2e (end-to-end tests)

This directory is intended for end-to-end test suites that exercise the
running application (optionally in Docker) through public HTTP endpoints.

- Keep scenarios realistic and independent
- Use unique ports/resources for parallelism
- Prefer cleanup hooks to avoid leftover containers/resources
