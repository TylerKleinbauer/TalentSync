from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import sqlite3
from config.settings import DATABASES
from backend.settings import JOB_ADS_EMBEDDINGS_PATH
from langchain_core.documents import Document
import logging
import traceback

# Django ORM imports
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from .models import Job

def embed_jobs(chroma_path = JOB_ADS_EMBEDDINGS_PATH, sqlite_path=DATABASES['jobs']):
    """
    Embeds new or updated job ads from SQLite and stores them in Chroma.
    
    Args:
        chroma_path (str): Path to the Chroma persistent store directory.
        sqlite_path (str): Path to the SQLite database containing job details.
    """
    logging.info("[EMBED_JOBS] Starting the embedding process with Chroma path: {chroma_path}, SQLite path: {sqlite_path}")
    
    # Initialize the embeddings
    try:
        embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
        logging.info("[EMBED_JOBS] OpenAIEmbeddings initialized successfully.")
        
        # Initialize Chroma with persistence
        vector_store = Chroma(
            collection_name="job_ads_embeddings",
            embedding_function=embeddings,
            persist_directory=chroma_path)
        logging.info("[EMBED_JOBS] Chroma vector store initialized successfully.")

        # Connect to SQLite
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        logging.info("[EMBED_JOBS] Connected to SQLite database successfully.")

        # Fetch jobs that are not yet embedded
        cursor.execute("SELECT id, company_name, template_title, template_title ||' ' || template_lead AS content FROM jobs")
        all_jobs = cursor.fetchall()
        logging.info(f"[EMBED_JOBS] Retrieved {len(all_jobs)} job ads from the database.")

        # Retrieve existing IDs from Chroma
        existing_ids = {id for id in vector_store.get(include=['documents'])['ids']}
        logging.info(f"[EMBED_JOBS] Retrieved {len(existing_ids)} existing job IDs from Chroma.")

        # Prepare new jobs for embedding
        new_jobs = [job for job in all_jobs if job[0] not in existing_ids]
        logging.info(f"[EMBED_JOBS] Found {len(new_jobs)} new job ads to embed.")

        if not new_jobs:
            logging.info("[EMBED_JOBS] No new jobs to embed. Exiting the embedding process.")
            conn.close()
            return

        # Process new jobs
        documents = []
        for id, company_name, template_title, content in new_jobs:
            try:
                doc_meta = {
                    'company_name': company_name or "",   # If None, store as ""
                    'job_title': template_title or ""
                }
                document = Document(
                    page_content=content,
                    metadata=doc_meta,
                    id = id
                )
                
                documents.append(document)
                # Generate embedding

                logging.debug(f"[EMBED_JOBS] Added job '{template_title}' with ID: {id} to the embedding queue.")

            except Exception as e:
                logging.error(f"[EMBED_JOBS] Failed to process job '{template_title}' with ID: {id}. Error: {e}")
                logging.debug(traceback.format_exc())

        try:
            vector_store.add_documents(documents=documents)
        except Exception as e:
            logging.error(f"[EMBED_JOBS] Failed to add documents to Chroma: {e}")
            logging.debug(traceback.format_exc())
    
        # Persist changes
        conn.close()
        logging.info(f"[EMBED_JOBS] Processed and embedded {len(new_jobs)} new job ads successfully.")
    
    except Exception as e:
        logging.error(f"[EMBED_JOBS] Embedding failed: {e}")
        logging.debug(traceback.format_exc())
        # Close the connection
        try:
            conn.close()
            logging.debug("[EMBED_JOBS] Closed SQLite database connection after an unexpected error.")
        except:
            pass


def embed_jobs_orm(chroma_path = JOB_ADS_EMBEDDINGS_PATH):
    """
    Embed new or updated job ads using Django ORM and store them in the Chroma vector store.

    Args:
        chroma_path (str): Path to the Chroma persistent store directory.
    """
    logging.info(f"[EMBED_JOBS_ORM] Starting embedding process with Chroma path: {chroma_path}")
    try:
        # Initialize embeddings using OpenAI's model.
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        logging.info("[EMBED_JOBS_ORM] OpenAIEmbeddings initialized successfully.")

        # Initialize Chroma with persistence.
        vector_store = Chroma(
            collection_name="job_ads_embeddings",
            embedding_function=embeddings,
            persist_directory=chroma_path,
        )
        logging.info("[EMBED_JOBS_ORM] Chroma vector store initialized successfully.")

        # Retrieve jobs from the database using Django ORM.
        # Concatenate template_title and template_lead to form the content.
        jobs_qs = Job.objects.annotate(
            content=Concat(
                "template_title",
                Value(" "),
                "template_lead",
                output_field=CharField()
            )
        ).values("id", "company_name", "template_title", "content")
        all_jobs = list(jobs_qs)
        logging.info(f"[EMBED_JOBS_ORM] Retrieved {len(all_jobs)} job ads from the database.")

        # Retrieve existing IDs from the vector store.
        try:
            existing_data = vector_store.get(include=["documents"])
            existing_ids = set(existing_data.get("ids", []))
        except Exception as e:
            logging.warning(f"[EMBED_JOBS_ORM] Failed to retrieve existing IDs from Chroma: {e}")
            existing_ids = set()
        logging.info(f"[EMBED_JOBS_ORM] Retrieved {len(existing_ids)} existing job IDs from Chroma.")

        # Filter for new jobs (those not already embedded).
        new_jobs = [job for job in all_jobs if job["id"] not in existing_ids]
        logging.info(f"[EMBED_JOBS_ORM] Found {len(new_jobs)} new job ads to embed.")

        documents = []
        for job in new_jobs:
            try:
                doc_meta = {
                    "company_name": job.get("company_name") or "",
                    "job_title": job.get("template_title") or "",
                }
                document = Document(
                    page_content=job.get("content"),
                    metadata=doc_meta,
                    id=job.get("id"),
                )
                documents.append(document)
                logging.debug(f"[EMBED_JOBS_ORM] Queued job '{job.get('template_title')}' with ID: {job.get('id')} for embedding.")
            except Exception as e:
                logging.error(f"[EMBED_JOBS_ORM] Error processing job ID {job.get('id')}: {e}")
                logging.debug(traceback.format_exc())

        if documents:
            try:
                vector_store.add_documents(documents=documents)
                logging.info(f"[EMBED_JOBS_ORM] Successfully embedded {len(documents)} job ads.")
            except Exception as e:
                logging.error(f"[EMBED_JOBS_ORM] Failed to add documents to Chroma: {e}")
                logging.debug(traceback.format_exc())
        else:
            logging.info("[EMBED_JOBS_ORM] No new documents to embed.")

    except Exception as e:
        logging.error(f"[EMBED_JOBS_ORM] Embedding process failed: {e}")
        logging.debug(traceback.format_exc())
