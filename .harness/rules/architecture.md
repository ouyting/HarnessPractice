# Architecture Rules

Harness V1 separates durable instructions (`rules`, `skills`, `workflows`) from mutable project knowledge (`memory`) and executable adapters (`tools`).

- Workflows define the order of work.
- Skills define how an operation is performed.
- Tools remain thin, local, and independently runnable.
- Memory records facts, not hidden reasoning.
