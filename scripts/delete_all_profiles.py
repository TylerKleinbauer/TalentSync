import sys
import os

root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from backend.apps.profile_agent.models import DBUserProfile

# Delete all existing profiles
DBUserProfile.objects.all().delete()
print("All profiles deleted successfully!") 