"""
Strategy Selector — Meta-cognitive Reasoning Strategy Selection
===============================================================
Decides which reasoning strategy to apply based on intent, context,
and cognitive node state.
Source: teonu-worldmodel + deer-flow.
"""

from enum import Enum
from typing import Dict, Any, List


class ReasoningStrategy(Enum):
    """Reasoning strategy enumeration."""
    DEDUCTIVE = "deductive"        # Derive from rules
    INDUCTIVE = "inductive"        # Generalise from observations
    ABDUCTIVE = "abductive"        # Infer cause from effect
    ANALOGICAL = "analogical"      # Find similar cases
    CAUSAL = "causal"              # Causal chain analysis
    MONTE_CARLO = "monte_carlo"   # Probabilistic simulation (L10 sandbox)
    SINGLE_PATH = "single"        # Conservative single path (degraded)


class StrategySelector:
    """
    Meta-cognitive strategy selector.
    Core question: "Given the current context, which reasoning strategy should apply?"

    Merged from:
    - teonu-worldmodel: meta-cognitive scheduling
    - deer-flow: DAG evaluation mechanism
    """

    def select(
        self,
        intent: str,
        context: Dict[str, Any],
        node_count: int = 0,
        avg_confidence: float = 0.5,
    ) -> ReasoningStrategy:
        """
        Select a reasoning strategy.

        Decision rules:
        - avg_confidence < 0.4  → SINGLE_PATH (conservative)
        - node_count > 5       → ABDUCTIVE (verify inferred nodes)
        - complexity keywords  → DEDUCTIVE (multi-path strategy)
        - default              → DEDUCTIVE
        """
        # Law: low confidence → conservative strategy
        if avg_confidence < 0.4:
            return ReasoningStrategy.SINGLE_PATH

        # Law: many inferred nodes → abductive verification
        if node_count > 5:
            return ReasoningStrategy.ABDUCTIVE

        # Complexity indicators → multi-path strategy
        complexity_indicators = [
            "分析", "评估", "比较", "预测", "权衡",
            "方案", "策略", "计划", "决策",
            "analyze", "evaluate", "compare", "predict", "assess",
            "plan", "strategy", "decide",
        ]
        if any(kw in intent for kw in complexity_indicators):
            return ReasoningStrategy.DEDUCTIVE

        # Default: deductive reasoning
        return ReasoningStrategy.DEDUCTIVE
