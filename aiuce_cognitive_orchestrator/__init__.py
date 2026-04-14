"""
aiuce-cognitive-orchestrator
============================
Meta-cognitive scheduling engine — DAG-based task orchestration with
three-system cognitive laws.

Exports:
    CognitiveOrchestrator  — Main cognitive orchestration engine
    CognitiveLaws          — Three-system cognitive laws
    StrategySelector       — Reasoning strategy selector
    TaskDAG                — Task DAG with topological sort
    TaskNode, CognitiveNode, NodeState — Core data classes
    ReasoningStrategy       — Reasoning strategy enum
"""

from .orchestrator import CognitiveOrchestrator
from .laws import CognitiveLaws
from .strategy import StrategySelector, ReasoningStrategy
from .dag import TaskNode, TaskDAG, CognitiveNode, CognitiveControl, NodeState

__version__ = "0.1.0"
__all__ = [
    "CognitiveOrchestrator",
    "CognitiveLaws",
    "StrategySelector",
    "TaskDAG",
    "TaskNode",
    "CognitiveNode",
    "NodeState",
    "ReasoningStrategy",
]
