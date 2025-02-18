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

from django.contrib.auth import get_user_model
User = get_user_model()

def view_latest_user():
    """
    Retrieves and displays the most recently created user from the database.
    """
    try:
        # Get the latest user based on date_joined timestamp
        latest_user = User.objects.latest('date_joined')
        
        # Display the user information
        print("\nLatest User:")
        print("=" * 50)
        print(f"User ID: {latest_user.id}")
        print(f"Username: {latest_user.username}")
        print(f"Email: {latest_user.email}")
        print(f"Date Joined: {latest_user.date_joined}")
        print(f"Last Login: {latest_user.last_login}")
        print(f"Is Staff: {latest_user.is_staff}")
        print(f"Is Active: {latest_user.is_active}")
        print(f"Is Superuser: {latest_user.is_superuser}")
        print("=" * 50)
        
        return latest_user
        
    except User.DoesNotExist:
        print("No users found in the database.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def view_all_users():
    """
    Retrieves and displays all users from the database, ordered by most recent first.
    """
    try:
        # Get all users, ordered by most recent first
        users = User.objects.all().order_by('-date_joined')
        
        if not users:
            print("No users found in the database.")
            return
            
        for user in users:
            print("\nUser:")
            print("=" * 50)
            print(f"User ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Date Joined: {user.date_joined}")
            print(f"Last Login: {user.last_login}")
            print(f"Is Staff: {user.is_staff}")
            print(f"Is Active: {user.is_active}")
            print(f"Is Superuser: {user.is_superuser}")
            
            # Try to get associated profile if it exists
            try:
                profile = user.profile
                print("\nAssociated Profile:")
                print(f"Profile Name: {profile.name}")
                print(f"Profile Created: {profile.created_at}")
                print(f"Profile Last Updated: {profile.updated_at}")
            except Exception:
                print("\nNo associated profile found")
                
            print("=" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("\nViewing latest user:")
    view_latest_user()
    
    # Uncomment the following lines if you want to see all users
    print("\nViewing all users:")
    view_all_users() 