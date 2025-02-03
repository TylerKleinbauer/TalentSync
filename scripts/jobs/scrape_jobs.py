import sys
import os
# Add the root directory to PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.job_scraping.jobs_functions import scrape_and_store_jobs
from config.settings import DATABASES

scrape_and_store_jobs(max_pages=200, published_since=3, db_path=DATABASES['jobs'])