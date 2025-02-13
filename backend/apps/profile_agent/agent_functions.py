# Import the necessary libraries
from langchain_core.messages import SystemMessage, HumanMessage
from asgiref.sync import sync_to_async
import uuid

# Import the agent classes
from backend.apps.profile_agent.agent_classes import ProfileState, UserProfile

# Import the LLM factory
from backend.apps.profile_agent.llm_config import LLMFactory

# Import the DB UserProfile model
from backend.apps.profile_agent.models import DBUserProfile


def create_profile(state: ProfileState) -> dict:
    """
    Creates a summary of the user's profile.

    Args:
    user_docs (List[str]): list of user documents

    Returns:
    str: user profile summary
    """

    system_message = """Your task is to create a detailed user work profile. The user has provided the following documents:
    A CV (please note the content of the CV may be in a strange order due to the format of the document. Please try to reconstruct it in a way that makes sense): 
    {cv}

    A cover letter: 
    {cover_letter}

    Take into consideration the optionally provided user feedback to improve the quality of the generated profile:

    {user_feedback}
    
    Please generate a detailed user profile based on these documents and optional feedback.
    The profile must include the following sections:
    (a) The user's name
    (b) Work experiences
    (c) Skills
    (d) Education
    (e) Certifications
    (f) Other information
    
    Be exhaustive and do not leave any important experience out.
    However, and this is crucial, do not invent anything. 
    If the provided documents and user feedback do not permit you to generate a section, leave it empty.
    I REPEAT: DO NOT INVENT ANY INFORMATION! LEAVE BLANK IF YOU CANNOT ANSWER!

    For example, do not write:
    - Sales Manager at ABC Company
    - Marketing Specialist at XYZ Company
    - Bachelors degree in Computer Science from ABC University
    
    Instead leave it blank.
    """

    system_message = system_message.format(
        cv=state['user_docs'][0],
        cover_letter=state['user_docs'][1], 
        user_feedback=state.get('user_feedback', '')
        )
        
    llm_factory = LLMFactory()
    llm = llm_factory.get_llm(model_key='gpt-4o')
    structured_llm = llm.with_structured_output(UserProfile)
    
    # Update the state with the generated base_profile
    detailed_profile= structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Can you generate the user profile please?")])

    return {"user_profile": detailed_profile}

def human_feedback(state: ProfileState):
    """ No-op node that should be interrupted on """
    print('Would you like to add something ?')
    pass

async def write_profile(state: ProfileState) -> None:
    """
    Writes the final user profile to the database.
    
    Args:
        state (ProfileState): Current state containing the user profile
    
    Returns:
        None
    """
    user_profile = state.get('user_profile')
    if user_profile:
        @sync_to_async
        def create_or_update_profile():
            try:
                # Generate a unique ID using UUID4
                unique_id = str(uuid.uuid4())
                
                DBUserProfile.objects.update_or_create(
                    id=unique_id,
                    defaults={
                        'name': user_profile.name,
                        'work_experience': user_profile.work_experience,
                        'skills': user_profile.skills, 
                        'education': user_profile.education,
                        'certifications': user_profile.certifications,
                        'other_info': user_profile.other_info
                    },
                )
            except Exception as e:
                print(f"Error updating or creating user profile: {e}")
                
        # Call the async function
        await create_or_update_profile()
    
    return {}

async def should_continue(state: ProfileState) -> str:
    """
    Determines the next node based on whether there is user feedback.
    
    Args:
        state (ProfileState): Current state
    
    Returns:
        str: Name of the next node to execute
    """
    # Check if human feedback is present
    human_feedback = state.get('user_feedback', None)
    if human_feedback:
        return "create_profile"
    
    # If no feedback, proceed to write the profile
    return "write_profile"