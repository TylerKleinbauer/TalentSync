# Import the necessary libraries
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display

# Import the agent classes
from backend.apps.profile_agent.agent_classes import ProfileState

# Import the agent functions
from backend.apps.profile_agent.agent_functions import create_profile, human_feedback, should_continue


def build_profile_graph():
    """
    Builds and returns the profile agent graph.
    
    Returns:
        tuple: A tuple containing (compiled_graph, memory_saver)
    """
    profile_builder = StateGraph(ProfileState)
    profile_builder.add_node("create_profile", create_profile)
    profile_builder.add_node('human_feedback', human_feedback)

    profile_builder.add_edge(START, "create_profile")
    profile_builder.add_edge('create_profile', 'human_feedback')
    profile_builder.add_conditional_edges('human_feedback', should_continue, ['create_profile', END])

    memory = MemorySaver()
    profile_graph = profile_builder.compile(checkpointer=memory, interrupt_before=['human_feedback'])
    
    return profile_graph, memory

# Optional: If you still want to display the graph when the module is run directly
if __name__ == "__main__":
    graph, _ = build_profile_graph()
    display(Image(graph.get_graph().draw_mermaid_png()))