"""
basic_usage.py — Basic usage examples for aiuce-cognitive-orchestrator.
Run: python examples/basic_usage.py
"""

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


def main():
    print("=" * 60)
    print("aiuce-cognitive-orchestrator — basic usage examples")
    print("=" * 60)

    # ── 1. Cognitive Laws ────────────────────────────────────────────────────
    print("\n[1] Three Cognitive Laws")
    print(f"    LWG_INFERENCE_MAX_CONFIDENCE = {CognitiveLaws.LWG_INFERENCE_MAX_CONFIDENCE}")
    print(f"    MAX_HISTORY                  = {CognitiveLaws.MAX_HISTORY}")
    print(f"    DEFAULT_TOKEN_BUDGET         = {CognitiveLaws.DEFAULT_TOKEN_BUDGET}")

    # ── 2. Cognitive Nodes ───────────────────────────────────────────────────
    print("\n[2] Cognitive Nodes")
    node = CognitiveNode(
        id="node-1",
        title="明天可能下雨",
        content="气象预报显示湿度升高，但尚未确认。",
        state=NodeState.INFERRED,
        confidence=0.5,
    )
    print(f"    Node: {node.title}")
    print(f"    Valid inference (Law I)? {node.is_valid_inference()}")
    print(f"    State: {node.state.value}, Confidence: {node.confidence}")

    # ── 3. Three-layer Cognitive Control ─────────────────────────────────────
    print("\n[3] Three-layer Cognitive Control")

    # ingest — what enters the cognitive world
    ingest = CognitiveControl.ingest_control("分析竞争对手策略", {})
    print(f"    ingest_control: allowed={ingest['allowed']}, stage={ingest['stage']}")

    # snapshot — budget-constrained context
    nodes = [
        CognitiveNode(id="s1", title="S1", content="stable content", state=NodeState.STABLE, confidence=0.9),
        CognitiveNode(id="i1", title="I1", content="inferred content", state=NodeState.INFERRED, confidence=0.5),
    ]
    snapshot = CognitiveControl.snapshot_control(nodes, token_budget=2000)
    print(f"    snapshot_control: {len(snapshot)} node(s) visible within budget")

    # reasoning — LWG inference validation
    reasoning = CognitiveControl.reasoning_control(nodes, "analyze")
    print(f"    reasoning_control: requires_validation={reasoning['requires_validation']}")

    # ── 4. Strategy Selection ────────────────────────────────────────────────
    print("\n[4] Strategy Selector")
    selector = StrategySelector()
    for intent in ["简单问答", "分析市场趋势", "预测下季度收入"]:
        strategy = selector.select(intent, {}, node_count=0, avg_confidence=0.7)
        print(f"    '{intent}' → {strategy.value}")

    # Low confidence → SINGLE_PATH
    low_conf = selector.select("复杂推理", {}, node_count=0, avg_confidence=0.2)
    print(f"    '复杂推理' (conf=0.2) → {low_conf.value}")

    # ── 5. Task DAG ──────────────────────────────────────────────────────────
    print("\n[5] Task DAG — build & sort")
    dag = TaskDAG(id="demo-dag")
    dag.add_node(TaskNode(id="root", label="Root", task="主任务", depends_on=[]))
    dag.add_node(TaskNode(id="sub1", label="分析", task="分析子任务", depends_on=["root"]))
    dag.add_node(TaskNode(id="sub2", label="比较", task="比较子任务", depends_on=["root"]))
    dag.add_node(TaskNode(id="join", label="汇总", task="汇总结果", depends_on=["sub1", "sub2"]))
    levels = dag.topological_sort()
    for i, level in enumerate(levels):
        print(f"    Level {i}: {level}")
    print(f"    DAG execution_order: {dag.execution_order}")

    # ── 6. CognitiveOrchestrator — plan & execute ────────────────────────────
    print("\n[6] CognitiveOrchestrator — full pipeline")
    orchestrator = CognitiveOrchestrator()  # no sovereignty gateway (optional)

    intent = "分析并比较 A/B 两种营销方案"
    print(f"    Intent: '{intent}'")
    planned_dag = orchestrator.plan(intent, {"token_budget": 3000})

    print(f"    DAG ID: {planned_dag.id}")
    for nid, node in planned_dag.nodes.items():
        print(f"      [{nid}] {node.label} | strategy={node.strategy.value} | layer={node.layer_tag} | deps={node.depends_on}")
    print(f"    Execution levels: {planned_dag.execution_order}")

    results = orchestrator.execute(planned_dag)
    print(f"    Execution results: {results}")

    # ── 7. Adding cognitive nodes to active store ────────────────────────────
    print("\n[7] Active cognitive node store")
    orchestrator.add_cognitive_node(
        CognitiveNode(id="fact-1", title="事实", content="地球是圆的", state=NodeState.STABLE, confidence=1.0)
    )
    print(f"    Active nodes: {list(orchestrator.active_nodes.keys())}")
    orchestrator.remove_cognitive_node("fact-1")
    print(f"    After removal: {list(orchestrator.active_nodes.keys())}")

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
