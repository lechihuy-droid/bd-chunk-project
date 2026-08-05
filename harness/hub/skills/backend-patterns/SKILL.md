---
name: backend-patterns
description: Apply backend architecture patterns for API design, database efficiency, and maintainable Node, Express, and Next.js API services.
---

# Backend Patterns

Use this skill when designing or reviewing backend behaviour, especially API
boundaries, data access, and service responsibilities.

1. Define the service boundary, callers, data ownership, and observable contract.
2. Model APIs around resources and user outcomes rather than storage details.
3. Validate input at boundaries and return clear, stable error semantics.
4. Keep transport handling, business rules, and data access separate.
5. Make authorization decisions close to the protected resource and action.
6. Design operations to be idempotent when retries or duplicate requests matter.
7. Use pagination, filtering, sorting, and limits deliberately for collections.
8. Avoid exposing internal fields, implementation details, or unnecessary data.
9. Choose data models and indexes from access patterns and consistency needs.
10. Watch for repeated queries, unbounded reads, and avoidable round trips.
11. Define transaction boundaries and recovery behaviour for multi-step changes.
12. Treat timeouts, partial failures, and concurrent updates as design cases.
13. Keep configuration, secrets, and environment-specific concerns outside domain
    logic.
14. Prefer simple, observable flows over clever abstractions.
15. State compatibility, migration, and operational risks before changing a
    public contract.

Do not claim an API, query, or service is safe or efficient without evidence.
