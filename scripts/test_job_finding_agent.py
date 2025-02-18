import sys
import os
from uuid import UUID

# Get the absolute path to the root directory ('Lucy')
root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from backend.apps.job_finding_agent.agent_graph import build_job_finding_graph
from backend.apps.job_finding_agent.agent_classes import MultiJobEvaluationState, UserProfile
from backend.apps.profile_agent.models import DBUserProfile
from django.contrib.auth import get_user_model

def test_job_finding_graph(user_id: str) -> None:
    """Test function for the job finding agent graph."""
    # Validate user_id is a valid UUID
    try:
        user_uuid = UUID(user_id)
        print(f"Valid user ID provided: {user_uuid}")
    except ValueError:
        print(f"Invalid user ID format: {user_id}")
        return
    
    # Initialize the graph
    graph = build_job_finding_graph()
    
    # Create initial state
    initial_state = MultiJobEvaluationState({
        "user_id": str(user_uuid),
        "user_profile": None,
        "similarity_search_profile": None,
        "job_ids": None,
        "job_info": None,
        "jobs": None,
        "job_evaluations": [],
        "user_feedback": None
    })
    
    # Create a new thread
    thread = {"configurable": {"thread_id": user_id}}
    
    # Start the graph execution
    print("Starting job finding process...")
    
    try:
        # Run the graph
        print("\nInvoking graph...")
        final_state = graph.invoke(initial_state, thread)
        
        print(f"Graph returned state with keys: {final_state.keys()}")
        
        # Print the job evaluations
        if final_state.get("job_evaluations") and final_state.get("job_info"):
            print("\nJob Evaluations:")
            print("=" * 50)
            
            # Create a dictionary of jobs for easy lookup
            jobs_dict = {job[0]: job for job in final_state["job_info"]}  # index 0 is job_id
            
            for evaluation in final_state["job_evaluations"]:
                # Get corresponding job info
                job_id = evaluation.job_id  # We'll need to add this to JobEvaluation
                job = jobs_dict.get(job_id)
                
                if job:
                    print("\nJob Details:")
                    print(f"ID: {job[0]}")
                    print(f"Company: {job[1]}")
                    print(f"Title: {job[2]}")
                    print(f"Description: {job[3][:200]}...")  # First 200 chars
                    print("\nEvaluation:")
                    print(f"Fit Score: {evaluation.fit_scores}")
                    print(f"Analysis:\n{evaluation.fit_evaluations}")
                else:
                    print(f"\nWarning: No job info found for evaluation {job_id}")
                print("-" * 30)
        else:
            print("\nNo job evaluations or job info found in final state")
            
    except Exception as e:
        print(f"Error during graph execution: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    # Test database connection
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
        
    # Get Tyler's user
    User = get_user_model()
    try:
        tyler_user = User.objects.get(email="tyler.kleinbauer@gmail.com")
        print(f"Found Tyler's user account with ID: {tyler_user.id}")
        
        # Verify the profile relationship
        try:
            profile = tyler_user.profile
            print("\nFound Tyler's existing profile:")
            print("=" * 50)
            print(f"Name: {profile.name}")
            print(f"Work Experience: {profile.work_experience[:100]}...")  # Show first 100 chars
            print(f"Skills: {profile.skills[:100]}...")
            print(f"Profile last updated: {profile.updated_at}")
            print("=" * 50)
            
            # Run the test with verified user ID
            print("\nStarting job finding test for Tyler...")
            test_job_finding_graph(str(tyler_user.id))
            
        except DBUserProfile.DoesNotExist:
            print("No profile found for Tyler. Please run test_profile_agent.py first to create a profile.")
            sys.exit(1)
            
    except User.DoesNotExist:
        print("Tyler's user account not found. Please ensure the user exists first.")
        sys.exit(1)