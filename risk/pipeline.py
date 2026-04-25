"""
LangGraph StateGraph for the risk assessment pipeline.
Entry point: invoke_pipeline(anomaly_event) -> RiskAssessmentDoc | None
"""
from typing import Any, Dict, Optional, TypedDict

try:
    from langgraph.graph import END, StateGraph
except ImportError:
    END = None
    StateGraph = None

from models.anomaly import AnomalyEvent
from models.patient import PatientHistory
from models.schemas import RiskAssessmentDoc
from risk.nodes import (
    emergency_flag,
    fetch_patient_history,
    publish_result,
    run_classify_risk,
    save_assessment_node,
)


class RiskPipelineState(TypedDict):
    anomaly: AnomalyEvent
    patient_history: Optional[PatientHistory]
    risk_assessment: Optional[RiskAssessmentDoc]
    emergency: bool
    error: Optional[str]


def _should_emergency_flag(state: RiskPipelineState) -> str:
    assessment = state.get("risk_assessment")
    if assessment and assessment.risk_score > 0.9:
        return "emergency"
    return "save"


def _build_graph() -> StateGraph:
    if StateGraph is None:
        raise RuntimeError("langgraph is not installed")
    graph = StateGraph(RiskPipelineState)

    graph.add_node("fetch_history", fetch_patient_history)
    graph.add_node("classify", run_classify_risk)
    graph.add_node("emergency_flag", emergency_flag)
    graph.add_node("save", save_assessment_node)
    graph.add_node("publish", publish_result)

    graph.set_entry_point("fetch_history")
    graph.add_edge("fetch_history", "classify")
    graph.add_conditional_edges(
        "classify",
        _should_emergency_flag,
        {"emergency": "emergency_flag", "save": "save"},
    )
    graph.add_edge("emergency_flag", "save")
    graph.add_edge("save", "publish")
    graph.add_edge("publish", END)

    return graph.compile()


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


async def invoke_pipeline(anomaly: AnomalyEvent) -> Optional[RiskAssessmentDoc]:
    initial_state: RiskPipelineState = {
        "anomaly": anomaly,
        "patient_history": None,
        "risk_assessment": None,
        "emergency": False,
        "error": None,
    }
    if StateGraph is None:
        state = fetch_patient_history(initial_state)
        state = run_classify_risk(state)
        if _should_emergency_flag(state) == "emergency":
            state = emergency_flag(state)
        state = save_assessment_node(state)
        state = publish_result(state)
        if state.get("error"):
            print(f"[PIPELINE ERROR] {state['error']}")
        return state.get("risk_assessment")

    graph = _get_graph()
    result = graph.invoke(initial_state)

    if result.get("error"):
        print(f"[PIPELINE ERROR] {result['error']}")

    return result.get("risk_assessment")
