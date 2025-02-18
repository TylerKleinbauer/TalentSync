from backend.apps.job_finding_agent.agent_functions import (
    retrieve_profile_from_db,
    prepare_profile_for_similarity_search,
    retrieve_id_similarity_search,
    retrieve_jobs_from_ids,
    send_to_evaluate_fit,
    evaluate_fit
)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display
from typing import Dict, Any

from backend.apps.job_finding_agent.agent_classes import MultiJobEvaluationState, SingleJobEvaluationState


def build_job_finding_graph():
    """
    Builds and returns the job finding agent graph.
    
    Returns:
        tuple: A tuple containing (compiled_graph, memory_saver)
    """
    job_finding_graph = StateGraph(MultiJobEvaluationState)
    
    # Add debug wrappers
    def debug_retrieve_profile_from_db(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting retrieve_profile_from_db node")
        return retrieve_profile_from_db(state)
    
    def debug_prepare_profile_for_similarity_search(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting prepare_profile_for_similarity_search node")
        return prepare_profile_for_similarity_search(state)
    
    def debug_retrieve_id_similarity_search(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting retrieve_id_similarity_search node")
        return retrieve_id_similarity_search(state)
    
    def debug_retrieve_jobs_from_ids(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting retrieve_jobs_from_ids node")
        return retrieve_jobs_from_ids(state)
    
    def debug_send_to_evaluate_fit(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting send_to_evaluate_fit node")
        return send_to_evaluate_fit(state)
    
    # Add nodes
    job_finding_graph.add_node("retrieve_profile_from_db", debug_retrieve_profile_from_db)
    job_finding_graph.add_node("prepare_profile_for_similarity_search", debug_prepare_profile_for_similarity_search)
    job_finding_graph.add_node("retrieve_id_similarity_search", debug_retrieve_id_similarity_search)
    job_finding_graph.add_node("retrieve_jobs_from_ids", debug_retrieve_jobs_from_ids)
    
    # Add the evaluate_fit node using the langgraph send API
    job_finding_graph.add_node("evaluate_fit", evaluate_fit)
    
    # Add edges
    job_finding_graph.add_edge(START, "retrieve_profile_from_db")
    job_finding_graph.add_edge("retrieve_profile_from_db", "prepare_profile_for_similarity_search")
    job_finding_graph.add_edge("prepare_profile_for_similarity_search", "retrieve_id_similarity_search")
    job_finding_graph.add_edge("retrieve_id_similarity_search", "retrieve_jobs_from_ids")
    job_finding_graph.add_conditional_edges("retrieve_jobs_from_ids", send_to_evaluate_fit)
    job_finding_graph.add_edge("evaluate_fit", END)

    memory = MemorySaver()
    job_finding_graph = job_finding_graph.compile(checkpointer=memory)
    
    return job_finding_graph



