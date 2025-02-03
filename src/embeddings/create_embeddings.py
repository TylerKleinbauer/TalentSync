from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import sqlite3
from config.settings import DATABASES
from langchain_core.documents import Document
import logging
import traceback

def embed_jobs(chroma_path = DATABASES['job_ads_embeddings'], sqlite_path=DATABASES['jobs']):
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


