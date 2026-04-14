# aiuce-cognitive-orchestrator

Meta-cognitive scheduling engine — DAG-based task orchestration with three-system cognitive laws.

## Overview

`aiuce-cognitive-orchestrator` provides a task orchestration engine for building structured, auditable cognitive pipelines. It decomposes natural-language intents into directed acyclic task graphs (DAGs), selects the optimal reasoning strategy per task, and enforces three ironclad cognitive laws at every stage.

## Three Cognitive Laws

| # | Law | Description |
|---|-----|-------------|
| I | **Assumption ≠ Fact** | LWG-generated inferences carry `confidence ≤ 0.6`; they are not facts until validated |
| II | **Cognition Must Be Compressible** | History > 10 entries → auto-summarise; pending timeout → forget or escalate |
| III | **Context Is Budget-Constrained** | Token budget exhaustion → preserve STABLE + high-confidence nodes first |

## Architecture

```
CognitiveOrchestrator
    ├── StrategySelector   → choose reasoning strategy
    ├── CognitiveControl   → ingest / snapshot / reasoning gates
    ├── TaskDAG            → DAG builder + topological sort
    └── SovereigntyGateway → optional L0 sovereignty gate
```

### Layers

| Layer | Module | Responsibility |
|-------|--------|----------------|
| L3 | `orchestrator.py` | Main planning/execution pipeline |
| L3 | `dag.py` | `TaskNode`, `TaskDAG`, `CognitiveNode`, `CognitiveControl` |
| L3 | `strategy.py` | `StrategySelector`, `ReasoningStrategy` |
| L3 | `laws.py` | `CognitiveLaws` constants |

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

## Optional: Plug in Sovereignty Gateway

```python
from aiuce_cognitive_orchestrator import CognitiveOrchestrator

# When sovereignty_gateway is None (default), the gate is bypassed.
# Pass a configured gateway to enforce L0 sovereignty checks:
# from my_package.l0_sovereignty_gateway import SovereigntyGateway
# orchestrator = CognitiveOrchestrator(sovereignty_gateway=SovereigntyGateway())

dag = orchestrator.plan("execute action", {"token_budget": 1500})
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
