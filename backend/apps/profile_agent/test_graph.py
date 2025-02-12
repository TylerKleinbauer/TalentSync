import sys
import os

# Get the absolute path to the root directory ('Lucy')
root_path = os.path.abspath(os.path.join(os.getcwd(), '../../../'))  # Adjust path to reach 'Lucy'
if root_path not in sys.path:
    sys.path.append(root_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

import asyncio
from typing import Optional
from .agent_graph import build_profile_graph
from .agent_classes import ProfileState

async def test_profile_graph(cv: str, cover_letter: str) -> None:
    """
    Test function for the profile agent graph.
    
    Args:
        cv (str): The user's CV text
        cover_letter (str): The user's cover letter text
    """
    # Initialize the graph
    graph, memory = build_profile_graph()
    
    # Create initial state
    initial_state = ProfileState({
        "user_docs": [cv, cover_letter],
        "user_profile": None,
        "user_feedback": ""
    })
    
    # Create a new thread
    thread = {"configurable": {"thread_id": "1"}}
    
    # Start the graph execution
    print("Starting profile generation...")
    
    async def run_with_feedback() -> None:
        while True:
            # Run the graph until it hits the human_feedback node
            final_state = await graph.ainvoke(initial_state, thread)
            
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
                initial_state["user_feedback"] = ""
                final_state = await graph.ainvoke(initial_state, thread)
                print("\nProfile saved to database. Process complete.")
                break
            elif response == 'y':
                print("\nPlease provide your feedback:")
                feedback = input().strip()
                initial_state["user_feedback"] = feedback
                print("\nProcessing feedback...")
            else:
                print("Invalid input. Please enter 'y' or 'n'")
                continue

    await run_with_feedback()

def run_test(cv: str, cover_letter: str) -> None:
    """
    Helper function to run the async test function.
    
    Args:
        cv (str): The user's CV text
        cover_letter (str): The user's cover letter text
    """
    asyncio.run(test_profile_graph(cv, cover_letter))

# Example usage
if __name__ == "__main__":
    
    from backend.apps.data_processing.process_documents import process_cv, process_cover_letter
    
    file_paths = [r"C:\Users\TylerKleinbauer\Dropbox\Tyler\Endeavors\Scripts\Lucy\user_docs\TK_CV_2024.pdf", 
                 r"C:\Users\TylerKleinbauer\Dropbox\Tyler\Endeavors\Scripts\Lucy\user_docs\TK_CoverLetter.pdf"]
    
    example_cv = process_cv(file_paths[0])
    example_cover_letter = process_cover_letter(file_paths[1])
    
    run_test(example_cv, example_cover_letter) 