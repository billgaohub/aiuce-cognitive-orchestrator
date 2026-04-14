"""
Tests for aiuce-cognitive-orchestrator.
"""

import pytest
import re

from aiuce_cognitive_orchestrator import (
    CognitiveOrchestrator,
    CognitiveLaws,
    StrategySelector,
    TaskDAG,
    TaskNode,
    CognitiveNode,
    NodeState,
    ReasoningStrategy,
)
from aiuce_cognitive_orchestrator.dag import CognitiveControl


# ── CognitiveLaws ─────────────────────────────────────────────────────────────

class TestCognitiveLaws:
    def test_laws_exist(self):
        assert CognitiveLaws.LWG_INFERENCE_MAX_CONFIDENCE == 0.6
        assert CognitiveLaws.MAX_HISTORY == 10
        assert CognitiveLaws.DEFAULT_TOKEN_BUDGET == 2000


# ── CognitiveNode ─────────────────────────────────────────────────────────────

class TestCognitiveNode:
    def test_valid_inference(self):
        node = CognitiveNode(
            id="n1",
            title="推断",
            content="明天可能下雨",
            state=NodeState.INFERRED,
            confidence=0.5,
        )
        assert node.is_valid_inference() is True

    def test_invalid_inference(self):
        node = CognitiveNode(
            id="n2",
            title="高置信推断",
            content="明天一定下雨",
            state=NodeState.INFERRED,
            confidence=0.9,
        )
        assert node.is_valid_inference() is False

    def test_draft_node_not_inference(self):
        node = CognitiveNode(
            id="n3",
            title="草稿",
            content="原始输入",
            state=NodeState.DRAFT,
            confidence=0.3,
        )
        assert node.is_valid_inference() is True  # not an inference, no violation


# ── CognitiveControl ──────────────────────────────────────────────────────────

class TestCognitiveControl:
    def test_ingest_control_no_gateway(self):
        result = CognitiveControl.ingest_control("hello", {})
        assert result["allowed"] is True
        assert result["stage"] == "ingested"

    def test_snapshot_control_empty(self):
        result = CognitiveControl.snapshot_control([])
        assert result == []

    def test_snapshot_control_respects_budget(self):
        nodes = [
            CognitiveNode(id="s1", title="S", content="x" * 10000, state=NodeState.STABLE),
            CognitiveNode(id="c1", title="C", content="y" * 10000, state=NodeState.CONFIRMED),
        ]
        result = CognitiveControl.snapshot_control(nodes, token_budget=2000)
        # Only STABLE fits within budget
        assert len(result) >= 1
        assert result[0].state == NodeState.STABLE

    def test_reasoning_control_no_violations(self):
        nodes = [
            CognitiveNode(id="r1", title="R", content="ok", state=NodeState.CONFIRMED, confidence=0.9),
        ]
        result = CognitiveControl.reasoning_control(nodes, "test intent")
        assert result["requires_validation"] is False
        assert result["lwg_violations"] == []

    def test_reasoning_control_detects_violations(self):
        nodes = [
            CognitiveNode(id="v1", title="V", content="bad", state=NodeState.INFERRED, confidence=0.9),
        ]
        result = CognitiveControl.reasoning_control(nodes, "test intent")
        assert result["requires_validation"] is True
        assert "v1" in result["lwg_violations"]


# ── TaskDAG ───────────────────────────────────────────────────────────────────

class TestTaskDAG:
    def test_add_node(self):
        dag = TaskDAG(id="t1")
        node = TaskNode(id="n1", label="t", task="do something")
        dag.add_node(node)
        assert "n1" in dag.nodes

    def test_topological_sort_single_level(self):
        dag = TaskDAG(id="t2")
        dag.add_node(TaskNode(id="a", label="A", task="task a"))
        dag.add_node(TaskNode(id="b", label="B", task="task b"))
        levels = dag.topological_sort()
        assert len(levels) == 1
        assert set(levels[0]) == {"a", "b"}

    def test_topological_sort_chain(self):
        dag = TaskDAG(id="t3")
        dag.add_node(TaskNode(id="root", label="Root", task="r", depends_on=[]))
        dag.add_node(TaskNode(id="mid", label="Mid", task="m", depends_on=["root"]))
        dag.add_node(TaskNode(id="leaf", label="Leaf", task="l", depends_on=["mid"]))
        levels = dag.topological_sort()
        assert levels[0] == ["root"]
        assert levels[1] == ["mid"]
        assert levels[2] == ["leaf"]

    def test_topological_sort_parallel(self):
        dag = TaskDAG(id="t4")
        dag.add_node(TaskNode(id="root", label="R", task="r", depends_on=[]))
        dag.add_node(TaskNode(id="p1", label="P1", task="p1", depends_on=["root"]))
        dag.add_node(TaskNode(id="p2", label="P2", task="p2", depends_on=["root"]))
        dag.add_node(TaskNode(id="join", label="J", task="j", depends_on=["p1", "p2"]))
        levels = dag.topological_sort()
        assert levels[0] == ["root"]
        assert set(levels[1]) == {"p1", "p2"}
        assert levels[2] == ["join"]


# ── StrategySelector ──────────────────────────────────────────────────────────

class TestStrategySelector:
    def test_low_confidence_single_path(self):
        selector = StrategySelector()
        s = selector.select("分析这件事", {}, node_count=0, avg_confidence=0.3)
        assert s == ReasoningStrategy.SINGLE_PATH

    def test_many_nodes_abductive(self):
        selector = StrategySelector()
        s = selector.select("简单问题", {}, node_count=10, avg_confidence=0.7)
        assert s == ReasoningStrategy.ABDUCTIVE

    def test_complex_intent_deductive(self):
        selector = StrategySelector()
        for kw in ["分析", "评估", "compare", "analyze"]:
            s = selector.select(f"{kw}这件事", {}, node_count=0, avg_confidence=0.7)
            assert s == ReasoningStrategy.DEDUCTIVE, f"Failed for keyword: {kw}"

    def test_default_deductive(self):
        selector = StrategySelector()
        s = selector.select("给我讲个笑话", {}, node_count=0, avg_confidence=0.7)
        assert s == ReasoningStrategy.DEDUCTIVE


# ── CognitiveOrchestrator ─────────────────────────────────────────────────────

class TestCognitiveOrchestrator:
    def test_plan_basic(self):
        orchestrator = CognitiveOrchestrator()
        dag = orchestrator.plan("给我讲个笑话")
        assert isinstance(dag, TaskDAG)
        assert len(dag.nodes) >= 1
        assert len(dag.execution_order) >= 1

    def test_plan_complex_task(self):
        orchestrator = CognitiveOrchestrator()
        dag = orchestrator.plan("分析并比较 A/B 两种方案")
        # Should produce root + sub-task node
        assert len(dag.nodes) >= 2

    def test_plan_injects_strategy(self):
        orchestrator = CognitiveOrchestrator()
        dag = orchestrator.plan("分析数据趋势", {"token_budget": 3000})
        root = dag.nodes.get(f"{dag.id}-root")
        assert root is not None
        assert isinstance(root.strategy, ReasoningStrategy)

    def test_execute_returns_results(self):
        orchestrator = CognitiveOrchestrator()
        dag = orchestrator.plan("简单任务")
        results = orchestrator.execute(dag)
        assert isinstance(results, dict)

    def test_add_remove_cognitive_node(self):
        orchestrator = CognitiveOrchestrator()
        node = CognitiveNode(id="cn1", title="T", content="C", state=NodeState.CONFIRMED)
        orchestrator.add_cognitive_node(node)
        assert "cn1" in orchestrator.active_nodes
        orchestrator.remove_cognitive_node("cn1")
        assert "cn1" not in orchestrator.active_nodes

    def test_plan_with_active_nodes_affects_strategy(self):
        orchestrator = CognitiveOrchestrator()
        for i in range(6):
            orchestrator.add_cognitive_node(
                CognitiveNode(id=f"an{i}", title=str(i), content="c", confidence=0.9)
            )
        # Many nodes → abductive strategy expected
        dag = orchestrator.plan("简单问题")
        root = dag.nodes.get(f"{dag.id}-root")
        assert root.strategy == ReasoningStrategy.ABDUCTIVE


# ── Snapshot Control Priority ──────────────────────────────────────────────────

class TestSnapshotControlPriority:
    def test_stable_preferred_over_inferred(self):
        nodes = [
            CognitiveNode(id="i1", title="I", content="x" * 1000, state=NodeState.INFERRED, confidence=0.6),
            CognitiveNode(id="st1", title="S", content="y" * 1000, state=NodeState.STABLE, confidence=0.9),
        ]
        # Very tight budget: only one node fits
        result = CognitiveControl.snapshot_control(nodes, token_budget=300)
        assert len(result) >= 1
        # STABLE should come before INFERRED
        stable_indices = [i for i, n in enumerate(result) if n.state == NodeState.STABLE]
        inferred_indices = [i for i, n in enumerate(result) if n.state == NodeState.INFERRED]
        if stable_indices and inferred_indices:
            assert stable_indices[0] < inferred_indices[0]
