import sys
import os

# Get the absolute path to the root directory ('Lucy')
root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from backend.apps.profile_agent.agent_graph import build_profile_graph
from backend.apps.profile_agent.agent_classes import ProfileState

def test_profile_graph(cv: str, cover_letter: str, user_id: str) -> None:
    """Test function for the profile agent graph."""
    # Initialize the graph
    graph = build_profile_graph()
    
    initial_run = True

    # Create initial state
    initial_state = ProfileState({
        "user_docs": [cv, cover_letter],
        "user_profile": None,
        "user_feedback": None,
        "user_id": user_id  # Add user_id to state
    })
    
    # Create a new thread
    thread = {"configurable": {"thread_id": user_id}}
    
    # Start the graph execution
    print("Starting profile generation...")
    
    while True:
        # Run the graph until it hits the human_feedback node
        print("\nInvoking graph...")
        if initial_run:
            final_state = graph.invoke(initial_state, thread)
            initial_run = False
        else:
            final_state = graph.invoke(None, thread)
        
        print(f"Graph returned state with keys: {final_state.keys()}")
        
        # Print the current profile
        current_profile = final_state["user_profile"]
        print("\nCurrent Profile:")
        print("=" * 50)
        print(f"Name: {current_profile.name}")
        print(f"\nWork Experience:\n{current_profile.work_experience}")
        print(f"\nSkills:\n{current_profile.skills}")
        print(f"\nEducation:\n{current_profile.education}")
        print(f"\nCertifications:\n{current_profile.certifications}")
        print(f"\nOther Info:\n{current_profile.other_info}")
        print("=" * 50)
        
        # Ask for feedback
        print("\nWould you like to provide feedback? (y/n)")
        response = input().lower().strip()
        
        if response == 'n':
            # Continue graph execution with empty feedback to trigger save and end
            print("\nNo more feedback, preparing to save profile...")
            graph.update_state(thread, {"user_feedback": None}, as_node="human_feedback")
            final_state = graph.invoke(None, thread)
            break
        elif response == 'y':
            print("\nPlease provide your feedback:")
            feedback = input().strip()
            graph.update_state(thread, {"user_feedback": feedback}, as_node="human_feedback")
            print("\nProcessing feedback...")
        else:
            print("Invalid input. Please enter 'y' or 'n'")
            continue

if __name__ == "__main__":
    # Test database connection and file
    try:
        from django.db import connection
        cursor = connection.cursor()
        print("Database connection successful!")
        
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'database.db')
        print(f"Database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}")
        print(f"Database is writable: {os.access(db_path, os.W_OK)}")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)
        
    # Get or create a test user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user, created = User.objects.get_or_create(
        id="c5e8e28a-92cd-4fb7-ace4-404298cba717",
        defaults={
            "email": "test@example.com",
            "is_staff": True
        }
    )
    
    from backend.apps.data_processing.process_documents import process_cv, process_cover_letter
    
    file_paths = [r"C:\Users\TylerKleinbauer\Dropbox\Tyler\Endeavors\Scripts\Lucy\user_docs\TK_CV_2024.pdf", 
                 r"C:\Users\TylerKleinbauer\Dropbox\Tyler\Endeavors\Scripts\Lucy\user_docs\TK_CoverLetter.pdf"]
    
    example_cv = process_cv(file_paths[0])
    example_cover_letter = process_cover_letter(file_paths[1])
    
    test_profile_graph(example_cv, example_cover_letter, str(test_user.id)) 