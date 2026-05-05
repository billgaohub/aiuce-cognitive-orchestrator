# aiuce-cognitive-orchestrator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Type](https://img.shields.io/badge/Type-Meta--Cognitive%20Scheduler-orange.svg)]()

**Meta-cognitive scheduling engine — DAG-based task orchestration with three-system cognitive laws.**

Decomposes natural-language intents into directed acyclic task graphs (DAGs), selects the optimal reasoning strategy per task, and enforces three ironclad cognitive laws at every stage.

## Three Cognitive Laws

| # | Law | Description |
|---|-----|-------------|
| I | **Assumption ≠ Fact** | LWG-generated inferences carry `confidence ≤ 0.6`; they are not facts until validated |
| II | **Cognition Must Be Compressible** | History > 10 entries → auto-summarise; pending timeout → forget or escalate |
| III | **Context Is Budget-Constrained** | Token budget exhaustion → preserve STABLE + high-confidence nodes first |

## Installation

```bash
pip install aiuce-cognitive-orchestrator
```

## Quick Start

```python
from aiuce_cognitive_orchestrator import CognitiveOrchestrator

orchestrator = CognitiveOrchestrator()

# Plan a task as a DAG
dag = orchestrator.plan("分析并比较 A/B 两种方案")
print(dag.execution_order)  # [['<root-id>'], ['<sub-id>']]

# Execute
results = orchestrator.execute(dag)
print(results)
```

## Architecture

```
CognitiveOrchestrator
    ├── StrategySelector   → choose reasoning strategy
    ├── CognitiveControl   → ingest / snapshot / reasoning gates
    ├── TaskDAG            → DAG builder + topological sort
    └── SovereigntyGateway → optional L0 sovereignty gate
```

## Reasoning Strategies

| Strategy | When to Use |
|----------|-------------|
| `DEDUCTIVE` | Rule-driven derivation (default) |
| `INDUCTIVE` | Generalise from observations |
| `ABDUCTIVE` | Infer cause from observed effect |
| `ANALOGICAL` | Find and apply similar cases |
| `CAUSAL` | Trace causal chains |
| `MONTE_CARLO` | Probabilistic simulation (L10 sandbox) |
| `SINGLE_PATH` | Conservative degraded mode (low confidence) |

## Node Lifecycle

```
DRAFT → INFERRED → CONFIRMED → STABLE
                    ↓
               DECAYED (obsolete)
```

## Running Tests

```bash
pip install pytest
pytest tests/
```

## License

MIT License — Copyright 2026 Bill Gao
