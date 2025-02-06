from django.core.management.base import BaseCommand
import logging
import traceback
from dotenv import load_dotenv

from backend.apps.job_scraping.clean_jobs_db import clean_databases_orm
from backend.apps.job_scraping.jobs_functions import scrape_and_store_jobs_orm
from backend.apps.job_scraping.create_embeddings import embed_jobs_orm
from backend.settings import JOB_ADS_EMBEDDINGS_PATH
from config.logging_config import setup_logging

class Command(BaseCommand):
    help = "Orchestrate the scraping, cleaning, and embedding and deleting of job data from Jobup."

    def handle(self, *args, **options):
        # Load environment variables from .env file.
        try:
            load_dotenv()
            logging.info("[JOBUP SCRAPING] Environment variables loaded successfully.")
        except Exception as e:
            logging.error(f"[JOBUP SCRAPING] Failed to load environment variables: {e}")
            logging.debug(traceback.format_exc())

        # Setup logging configuration.
        try:
            setup_logging()
            logging.info("[JOBUP SCRAPING] Logging has been configured.")
        except Exception as e:
            logging.error(f"[JOBUP SCRAPING] Failed to setup logging: {e}")
            logging.debug(traceback.format_exc())

        # Clean database and vector store.
        try:
            logging.info("[JOBUP SCRAPING] Starting database cleaning process.")
            clean_databases_orm(chroma_path=JOB_ADS_EMBEDDINGS_PATH)
            logging.info("[JOBUP SCRAPING] Database cleaning completed successfully.")
        except Exception as e:
            logging.error(f"[JOBUP SCRAPING] Database cleaning failed: {e}")
            logging.debug(traceback.format_exc())

        # Scrape jobs.
        try:
            logging.info("[JOBUP SCRAPING] Starting job scraping process.")
            scrape_and_store_jobs_orm(max_pages=200, published_since=3)
            logging.info("[JOBUP SCRAPING] Job scraping process completed successfully.")
        except Exception as e:
            logging.error(f"[JOBUP SCRAPING] Job scraping failed: {e}")
            logging.debug(traceback.format_exc())

        # Embed jobs.
        try:
            logging.info("[JOBUP SCRAPING] Starting job embedding process.")
            embed_jobs_orm(chroma_path=JOB_ADS_EMBEDDINGS_PATH)
            logging.info("[JOBUP SCRAPING] Job embedding process completed successfully.")
        except Exception as e:
            logging.error(f"[JOBUP SCRAPING] Job embedding failed: {e}")
            logging.debug(traceback.format_exc())
