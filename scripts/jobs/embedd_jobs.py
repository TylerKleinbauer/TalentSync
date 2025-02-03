from dotenv import load_dotenv
from config.settings import DATABASES
from src.embeddings.create_embeddings import embed_jobs
import sys
import os
# Add the root directory to PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.job_scraping.jobs_functions import scrape_and_store_jobs
from config.settings import DATABASES

load_dotenv()

#chroma_path = DATABASES['job_ads_embeddings']
embed_jobs(chroma_path=DATABASES['job_ads_embeddings'], sqlite_path=DATABASES['jobs'])