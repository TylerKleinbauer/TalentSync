import sys
import os

root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.db import connection

def check_db_tables():
    """List all tables in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name;
        """)
        tables = cursor.fetchall()
        
        print("\nExisting tables in database:")
        print("=" * 50)
        for table in tables:
            print(table[0])
        print("=" * 50)

if __name__ == "__main__":
    check_db_tables() 