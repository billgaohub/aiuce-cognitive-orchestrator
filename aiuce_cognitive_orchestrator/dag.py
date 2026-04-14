"""
Task DAG — Directed Acyclic Graph with Topological Sort
=======================================================
Task node definition, DAG construction, and topological execution ordering.
Also includes CognitiveNode and NodeState for cognitive state management.
Source: teonu-worldmodel + deer-flow.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .laws import CognitiveLaws
from .strategy import ReasoningStrategy


# ── Cognitive Node State ──────────────────────────────────────────────────────

class NodeState(Enum):
    """Cognitive node lifecycle states."""
    DRAFT = "draft"            # Draft, pending validation
    INFERRED = "inferred"      # LWG-generated inference, confidence <= 0.6
    CONFIRMED = "confirmed"    # Validated, trusted
    STABLE = "stable"          # Stable, usable as reasoning premise
    DECAYED = "decayed"        # Obsolete / forgotten


@dataclass
class CognitiveNode:
    """
    Cognitive node — a unit of knowledge or belief in the cognitive world.
    """
    id: str
    title: str
    content: str
    state: NodeState = NodeState.DRAFT
    confidence: float = 0.5
    half_life_days: int = 30
    layer_tags: List[str] = field(default_factory=list)   # Layer attribution (L0-L10)
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def is_valid_inference(self) -> bool:
        """Law I: inferred node confidence must not exceed the maximum."""
        return self.confidence <= CognitiveLaws.LWG_INFERENCE_MAX_CONFIDENCE


# ── Cognitive Control ──────────────────────────────────────────────────────────

class CognitiveControl:
    """
    Three-layer cognitive control functions.
    Each layer corresponds to a distinct control gate.
    """

    @staticmethod
    def ingest_control(
        intent: str,
        context: Dict[str, Any],
        sovereignty_gateway=None,
    ) -> Dict[str, Any]:
        """
        Ingest gate — decides what enters the cognitive world.

        Optional sovereignty gateway integration:
            from aiuce_cognitive_orchestrator.l0_sovereignty_gateway import SovereigntyGateway
            gateway = SovereigntyGateway()
            result = CognitiveControl.ingest_control(intent, ctx, sovereignty_gateway=gateway)
        """
        if sovereignty_gateway is not None:
            sv = sovereignty_gateway.audit(intent, context)
            if sv.vetoed:
                return {
                    "allowed": False,
                    "gate": "sovereignty",
                    "reason": sv.reason,
                    "stage": "denied",
                }

        # Default: allow if no gateway is configured
        return {
            "allowed": True,
            "gate": "passed",
            "confidence": 1.0,
            "stage": "ingested",
        }

    @staticmethod
    def snapshot_control(
        nodes: List[CognitiveNode],
        token_budget: int = CognitiveLaws.DEFAULT_TOKEN_BUDGET,
    ) -> List[CognitiveNode]:
        """
        Snapshot gate — decides what the current reasoning world can see.

        Priority order: STABLE > CONFIRMED > INFERRED > DRAFT
        When over budget, prune from lowest priority upward.
        """
        if not nodes:
            return []

        def priority(node: CognitiveNode) -> tuple:
            state_order = {
                NodeState.STABLE: 0,
                NodeState.CONFIRMED: 1,
                NodeState.INFERRED: 2,
                NodeState.DRAFT: 3,
                NodeState.DECAYED: 99,
            }
            return (state_order.get(node.state, 99), -node.confidence)

        sorted_nodes = sorted(nodes, key=priority)

        # Rough token estimate: characters / 4
        total_tokens = sum(len(n.content) // 4 for n in sorted_nodes)
        if total_tokens <= token_budget:
            return sorted_nodes

        budget_nodes: List[CognitiveNode] = []
        used_tokens = 0
        for node in sorted_nodes:
            node_tokens = len(node.content) // 4
            if used_tokens + node_tokens <= token_budget:
                budget_nodes.append(node)
                used_tokens += node_tokens
            elif not budget_nodes:
                # Always include at least the highest-priority node
                budget_nodes.append(node)
                break
            else:
                break

        return budget_nodes

    @staticmethod
    def reasoning_control(
        nodes: List[CognitiveNode],
        intent: str,
    ) -> Dict[str, Any]:
        """
        Reasoning gate (LWG — Local World Generation).

        Core rule: when generating inferences, Law I must hold.
        Inferred nodes must have confidence <= 0.6 and carry requires_validation flag.
        """
        valid_nodes = [n for n in nodes if n.state != NodeState.DECAYED]

        violations = []
        for node in valid_nodes:
            if node.state == NodeState.INFERRED and not node.is_valid_inference():
                violations.append(node.id)

        return {
            "valid_nodes": valid_nodes,
            "lwg_violations": violations,
            "requires_validation": len(violations) > 0,
            "inference_count": sum(1 for n in valid_nodes if n.state == NodeState.INFERRED),
        }


# ── Task Node & DAG ────────────────────────────────────────────────────────────

@dataclass
class TaskNode:
    """
    DAG task node — represents a decomposable sub-task.
    """
    id: str
    label: str
    task: str
    strategy: ReasoningStrategy = ReasoningStrategy.DEDUCTIVE
    depends_on: List[str] = field(default_factory=list)   # Predecessor node IDs
    confidence: float = 0.5
    status: str = "pending"      # pending | running | done | failed
    result: Any = None
    layer_tag: str = ""         # AIUCE Layer attribution (L0-L10)


@dataclass
class TaskDAG:
    """
    Task DAG — directed acyclic graph of task nodes.
    Supports topological sort for parallel/serial execution scheduling.
    """
    id: str
    nodes: Dict[str, TaskNode] = field(default_factory=dict)
    execution_order: List[List[str]] = field(default_factory=list)   # Per-level groupings

    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the DAG."""
        self.nodes[node.id] = node

    def topological_sort(self) -> List[List[str]]:
        """
        Topological sort using Kahn's algorithm.
        Returns node IDs grouped by execution level (parallel-safe within each level).
        Detects cycles: if unvisited nodes remain with no zero-in-degree, a cycle exists.
        """
        in_degree = {nid: len(n.depends_on) for nid, n in self.nodes.items()}
        levels: List[List[str]] = []
        remaining = set(self.nodes.keys())

        while remaining:
            current_level = [nid for nid in remaining if in_degree[nid] == 0]
            if not current_level:
                # Cycle detected — remaining nodes form a cycle
                break
            levels.append(current_level)
            for nid in current_level:
                remaining.remove(nid)
                for successor_id, succ in self.nodes.items():
                    if nid in succ.depends_on:
                        in_degree[successor_id] -= 1

        self.execution_order = levels
        return levels
