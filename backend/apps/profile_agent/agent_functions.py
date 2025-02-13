# Import the necessary libraries
from langchain_core.messages import SystemMessage, HumanMessage
import uuid
from django.db import transaction

# Import the agent classes
from backend.apps.profile_agent.agent_classes import ProfileState, UserProfile

# Import the LLM factory
from config.llm_config import LLMFactory

# Import the DB UserProfile model
from backend.apps.profile_agent.models import DBUserProfile

# Import the User model
from backend.apps.users.models import User



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
    
    detailed_profile = structured_llm.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Can you generate the user profile please?")
    ])

    return {"user_profile": detailed_profile}

def human_feedback(state: ProfileState):
    """ No-op node that should be interrupted on """
    pass

def write_profile(state: ProfileState) -> dict:
    """Writes the final user profile to the database."""
    print("\nEntering write_profile function")
    user_profile = state.get('user_profile')
    user_id = state.get('user_id')
    
    if user_profile:
        try:
            with transaction.atomic():
                # Get or create user
                user = User.objects.get(id=user_id)
                
                profile, created = DBUserProfile.objects.update_or_create(
                    user=user,  # Use user instead of generating new ID
                    defaults={
                        'name': user_profile.name,
                        'work_experience': user_profile.work_experience,
                        'skills': user_profile.skills, 
                        'education': user_profile.education,
                        'certifications': user_profile.certifications,
                        'other_info': user_profile.other_info
                    },
                )
                
                print(f"Profile {'created' if created else 'updated'} successfully!")
            return None
            
        except Exception as e:
            print(f"Error updating or creating user profile: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return None
    else:
        print("No user profile found in state")
        return None

def should_continue(state: ProfileState) -> str:
    """Determines the next node based on whether there is user feedback."""
    # Check if human feedback is present
    human_feedback = state.get('user_feedback', None)
    print(f"\nIn should_continue function:")
    print(f"User feedback: {human_feedback}")
    if human_feedback:
        print("Routing to create_profile")
        return "create_profile"
    
    print("Routing to write_profile")
    return "write_profile"