# Import the necessary libraries
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display
from typing import Dict, Any

# Import the agent classes
from backend.apps.profile_agent.agent_classes import ProfileState

# Import the agent functions
from backend.apps.profile_agent.agent_functions import (
    create_profile, 
    human_feedback, 
    should_continue, 
    write_profile,
    profile_exists,
    edit_profile
)


def build_profile_graph():
    """
    Builds and returns the profile agent graph.
    
    Returns:
        tuple: A tuple containing (compiled_graph, memory_saver)
    """
    profile_builder = StateGraph(ProfileState)
    
    # Add debug wrappers
    def debug_create_profile(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting create_profile node")
        return create_profile(state)
    
    def debug_human_feedback(state: Dict[str, Any]) -> None:
        print("\nExecuting human_feedback node")
        return human_feedback(state)
    
    def debug_write_profile(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting write_profile node")
        return write_profile(state)
    
    def debug_profile_exists(state: Dict[str, Any]) -> str:
        print("\nExecuting profile_exists node")
        return profile_exists(state)
    
    def debug_edit_profile(state: Dict[str, Any]) -> Dict[str, Any]:
        print("\nExecuting edit_profile node")
        return edit_profile(state)
    
    def debug_should_continue(state: Dict[str, Any]) -> str:
        print("\nExecuting should_continue node")
        return should_continue(state)
    
    # Add nodes
    profile_builder.add_node("profile_exists", debug_profile_exists)
    profile_builder.add_node("create_profile", debug_create_profile)
    profile_builder.add_node('human_feedback', debug_human_feedback)
    profile_builder.add_node('edit_profile', debug_edit_profile)
    profile_builder.add_node('write_profile', debug_write_profile)

    # Add edges
    profile_builder.add_edge(START, "profile_exists")
    profile_builder.add_conditional_edges("profile_exists", debug_profile_exists,["create_profile", "human_feedback"])
    profile_builder.add_edge('create_profile', 'human_feedback')
    profile_builder.add_edge('human_feedback', 'edit_profile')
    profile_builder.add_conditional_edges('edit_profile',debug_should_continue,["human_feedback", "write_profile"])
    profile_builder.add_edge('write_profile', END)

    memory = MemorySaver()
    profile_graph = profile_builder.compile(
        checkpointer=memory, 
        interrupt_before=['human_feedback']
    )
    
    return profile_graph