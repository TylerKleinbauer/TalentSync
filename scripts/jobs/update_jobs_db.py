import sys
import os
from dotenv import load_dotenv
import logging

# Add the root directory to PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from src.job_scraping.jobs_functions import scrape_and_store_jobs
from config.settings import DATABASES
from src.embeddings.create_embeddings import embed_jobs
from config.logging_config import setup_logging
from src.job_scraping.clean_jobs_db import clean_databases

def main():
    """
    Main function to orchestrate the scraping, cleaning, and embedding of job data from Jobup.
    """
    # Load environment variables from .env file
    load_dotenv()
    logging.info("[JOBUP SCRAPING] Environment variables loaded successfully.")

    # Setup logging configuration
    setup_logging()
    logging.info("[JOBUP SCRAPING] Logging has been configured.")

    # Clean database
    try:
        logging.info("[JOBUP SCRAPING] Starting database cleaning process.")
        clean_databases(sqlite_path=DATABASES['jobs'], chroma_path=DATABASES['job_ads_embeddings'])
        logging.info("[JOBUP SCRAPING] Database cleaning completed successfully.")
    except Exception as e:
        logging.error(f"[JOBUP SCRAPING] Database cleaning failed: {e}")
        logging.debug(traceback.format_exc())

    # Scrape jobs
    try:
        logging.info("[JOBUP SCRAPING] Starting job scraping process.")
        scrape_and_store_jobs(max_pages=200, published_since=3, db_path=DATABASES['jobs'])
        logging.info("[JOBUP SCRAPING] Job scraping process completed successfully.")
    except Exception as e:
        logging.error(f"[JOBUP SCRAPING] Job scraping failed: {e}")
        logging.debug(traceback.format_exc())

    # Embed jobs
    try:
        logging.info("[JOBUP SCRAPING] Starting job embedding process.")
        embed_jobs(chroma_path=DATABASES['job_ads_embeddings'], sqlite_path=DATABASES['jobs'])
        logging.info("[JOBUP SCRAPING] Job embedding process completed successfully.")
    except Exception as e:
        logging.error(f"[JOBUP SCRAPING] Job embedding failed: {e}")
        logging.debug(traceback.format_exc())

if __name__ == "__main__":
    import traceback
    main()
