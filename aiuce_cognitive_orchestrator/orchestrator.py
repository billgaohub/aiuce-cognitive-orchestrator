"""
Cognitive Orchestrator — Meta-cognitive Task Orchestration Engine
================================================================
Main entry point for DAG-based cognitive task planning and execution.

Design principles:
1. Meta-cognitive scheduling (StrategySelector): choose strategy before reasoning
2. Three-layer cognitive control: ingest → snapshot → LWG
3. DAG task orchestration: decompose intent into parallelisable task graph
4. Optional L0 sovereignty gate: plug in SovereigntyGateway to enforce
   sovereignty checks before DAG execution

Source: teonu-worldmodel + deer-flow.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid
import re

from .laws import CognitiveLaws
from .strategy import StrategySelector, ReasoningStrategy
from .dag import TaskNode, TaskDAG, CognitiveNode, CognitiveControl, NodeState


class CognitiveOrchestrator:
    """
    Cognitive orchestrator — coordinates planning and execution of
    DAG-structured cognitive tasks.

    Args:
        sovereignty_gateway: Optional SovereigntyGateway instance.
            When provided, each task node in the DAG is checked against
            the sovereignty gate before execution.
            Example::
                from aiuce_cognitive_orchestrator.l0_sovereignty_gateway import SovereigntyGateway
                orchestrator = CognitiveOrchestrator(sovereignty_gateway=SovereigntyGateway())
    """

    def __init__(self, sovereignty_gateway=None):
        self.sovereignty_gateway = sovereignty_gateway
        self.strategy_selector = StrategySelector()
        self.active_nodes: Dict[str, CognitiveNode] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def plan(self, intent: str, context: Dict[str, Any] = None) -> TaskDAG:
        """
        Main entry point — plan a cognitive task as a DAG.

        Pipeline:
          1. Meta-cognitive scheduling  → choose reasoning strategy
          2. Ingest control             → gate what enters the cognitive world
          3. Snapshot control           → budget-constrained context window
          4. Reasoning control           → validate LWG inference compliance
          5. DAG decomposition           → split intent into task nodes
          6. Sovereignty gate (opt.)   → veto any non-compliant task nodes

        Args:
            intent: Natural-language task intent.
            context: Optional runtime context (token_budget, etc.).

        Returns:
            TaskDAG: A DAG representing the planned task decomposition.

        Raises:
            PermissionError: If ingest control rejects the intent.
        """
        context = context or {}

        # ── Stage 1: Meta-cognitive scheduling ──────────────────────────────
        node_count = len(self.active_nodes)
        avg_conf = (
            sum(n.confidence for n in self.active_nodes.values()) / max(node_count, 1)
        )
        strategy = self.strategy_selector.select(intent, context, node_count, avg_conf)

        # ── Stage 2: Ingest gate ───────────────────────────────────────────
        ingest = CognitiveControl.ingest_control(
            intent,
            context,
            sovereignty_gateway=self.sovereignty_gateway,
        )
        if not ingest.get("allowed", False):
            raise PermissionError(f"L3 planning rejected by ingest gate: {ingest}")

        # ── Stage 3: Snapshot gate ─────────────────────────────────────────
        snapshot = CognitiveControl.snapshot_control(
            list(self.active_nodes.values()),
            token_budget=context.get("token_budget", CognitiveLaws.DEFAULT_TOKEN_BUDGET),
        )

        # ── Stage 4: Reasoning gate ─────────────────────────────────────────
        reasoning = CognitiveControl.reasoning_control(snapshot, intent)
        if reasoning.get("requires_validation", False):
            # Flag violations but do not block
            pass

        # ── Stage 5: DAG decomposition ──────────────────────────────────────
        dag = self._decompose(intent, strategy, context)

        # ── Stage 6: Sovereignty gate (optional) ────────────────────────────
        if self.sovereignty_gateway is not None:
            for node in dag.nodes.values():
                veto = self.sovereignty_gateway.audit(node.task)
                if veto.vetoed:
                    node.status = "failed"
                    node.result = {"error": f"Sovereignty veto: {veto.reason}"}

        return dag

    def execute(self, dag: TaskDAG) -> Dict[str, Any]:
        """
        Execute a planned TaskDAG.

        Nodes within the same topological level are parallelisable.
        Nodes across levels execute sequentially in level order.

        Args:
            dag: A TaskDAG returned by plan().

        Returns:
            Dict mapping node_id → execution result (or None if skipped/failed).
        """
        results = {}
        for level in dag.execution_order:
            for node_id in level:
                node = dag.nodes[node_id]
                if node.status == "failed":
                    continue

                node.status = "running"
                # TODO: invoke actual LLM or tool harness here
                node.status = "done"
                results[node_id] = node.result

        return results

    def add_cognitive_node(self, node: CognitiveNode) -> None:
        """Add a cognitive node to the active node store."""
        self.active_nodes[node.id] = node

    def remove_cognitive_node(self, node_id: str) -> None:
        """Remove a cognitive node from the active node store."""
        self.active_nodes.pop(node_id, None)

    # ── Private: DAG decomposition ────────────────────────────────────────────

    SUB_TASK_PATTERNS = [
        (re.compile(r"分析[和并]?比较"), "分析子任务", "L3"),
        (re.compile(r"规划和?实施"), "规划子任务", "L7"),
        (re.compile(r"执行和?验证"), "执行子任务", "L9"),
        (re.compile(r"监控和?调整"), "监控子任务", "L6"),
    ]

    def _decompose(
        self,
        intent: str,
        strategy: ReasoningStrategy,
        context: Dict[str, Any],
    ) -> TaskDAG:
        """
        Decompose a task intent into a DAG of sub-tasks.

        Simple strategy: creates a single root node.
        On complex-task pattern match: adds parallel sub-task nodes
        that depend on the root node.
        """
        dag_id = str(uuid.uuid4())[:8]
        dag = TaskDAG(id=dag_id, nodes={})

        # Root task node
        root = TaskNode(
            id=f"{dag_id}-root",
            label="主任务",
            task=intent,
            strategy=strategy,
            layer_tag="L3",
        )
        dag.add_node(root)

        # Complex task: split into sub-tasks
        for pattern, label, layer in self.SUB_TASK_PATTERNS:
            if pattern.search(intent):
                sub = TaskNode(
                    id=f"{dag_id}-sub-{len(dag.nodes)}",
                    label=label,
                    task=intent,
                    strategy=strategy,
                    depends_on=[root.id],
                    layer_tag=layer,
                )
                dag.add_node(sub)

        dag.topological_sort()
        return dag
