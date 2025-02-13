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

def view_latest_profile():
    """
    Retrieves and displays the most recently updated profile from the database.
    """
    try:
        # Get the latest profile based on updated_at timestamp
        latest_profile = DBUserProfile.objects.latest('updated_at')
        
        # Display the profile information
        print("\nLatest Profile:")
        print("=" * 50)
        print(f"Profile ID: {latest_profile.id}")
        print(f"Last Updated: {latest_profile.updated_at}")
        print(f"Created At: {latest_profile.created_at}")
        print("=" * 50)
        print(f"Name: {latest_profile.name}")
        print(f"\nWork Experience:\n{latest_profile.work_experience}")
        print(f"\nSkills:\n{latest_profile.skills}")
        print(f"\nEducation:\n{latest_profile.education}")
        print(f"\nCertifications:\n{latest_profile.certifications}")
        print(f"\nOther Info:\n{latest_profile.other_info}")
        print("=" * 50)
        
        return latest_profile
        
    except DBUserProfile.DoesNotExist:
        print("No profiles found in the database.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def view_all_profiles():
    """
    Retrieves and displays all profiles from the database, ordered by most recent first.
    """
    try:
        # Get all profiles, ordered by most recent first
        profiles = DBUserProfile.objects.all().order_by('-updated_at')
        
        if not profiles:
            print("No profiles found in the database.")
            return
            
        for profile in profiles:
            print("\nProfile:")
            print("=" * 50)
            print(f"Profile ID: {profile.id}")
            print(f"Last Updated: {profile.updated_at}")
            print(f"Created At: {profile.created_at}")
            print("=" * 50)
            print(f"Name: {profile.name}")
            print(f"\nWork Experience:\n{profile.work_experience}")
            print(f"\nSkills:\n{profile.skills}")
            print(f"\nEducation:\n{profile.education}")
            print(f"\nCertifications:\n{profile.certifications}")
            print(f"\nOther Info:\n{profile.other_info}")
            print("=" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("\nViewing latest profile:")
    view_latest_profile()
    
    # Uncomment the following lines if you want to see all profiles
    # print("\nViewing all profiles:")
    # view_all_profiles() 