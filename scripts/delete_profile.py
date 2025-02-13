import sys
import os

# Get the absolute path to the root directory ('Lucy')
root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from backend.apps.profile_agent.models import DBUserProfile

def delete_profile(profile_id: str) -> bool:
    """
    Deletes a user profile from the database by ID.
    
    Args:
        profile_id (str): The UUID of the profile to delete
        
    Returns:
        bool: True if profile was deleted, False otherwise
    """
    try:
        # Try to get the profile
        profile = DBUserProfile.objects.get(id=profile_id)
        
        # Print profile info before deletion
        print(f"\nFound profile:")
        print("=" * 50)
        print(f"Profile ID: {profile.id}")
        print(f"Name: {profile.name}")
        print("=" * 50)
        
        # Confirm deletion
        confirm = input("\nAre you sure you want to delete this profile? (y/n): ").lower().strip()
        if confirm == 'y':
            profile.delete()
            print(f"\nProfile {profile_id} has been deleted.")
            return True
        else:
            print("\nDeletion cancelled.")
            return False
            
    except DBUserProfile.DoesNotExist:
        print(f"\nNo profile found with ID: {profile_id}")
        return False
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return False

def list_profiles():
    """Lists all profiles in the database with their IDs."""
    try:
        profiles = DBUserProfile.objects.all().order_by('-updated_at')
        if not profiles:
            print("\nNo profiles found in the database.")
            return
            
        print("\nAvailable profiles:")
        print("=" * 50)
        for profile in profiles:
            print(f"ID: {profile.id}")
            print(f"Name: {profile.name}")
            print(f"Last Updated: {profile.updated_at}")
            print("-" * 30)
            
    except Exception as e:
        print(f"\nAn error occurred while listing profiles: {str(e)}")

if __name__ == "__main__":
    # First list all available profiles
    list_profiles()
    
    # Ask for profile ID to delete
    profile_id = input("\nEnter the ID of the profile to delete (or press Enter to cancel): ").strip()
    
    if profile_id:
        delete_profile(profile_id)
    else:
        print("\nOperation cancelled.") 