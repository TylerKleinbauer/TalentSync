import sqlite3
from config.settings import DATABASES
import requests
from urllib.parse import urlparse
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def get_ids_to_delete(sqlite_path=DATABASES['jobs']):
    """
    Identifies and logs invalid job posting URLs in a SQLite database, with fallback mechanisms for handling SSL errors
    and retrying using a secondary URL.

    This function checks the validity of job posting URLs stored in a SQLite database. It performs the following steps:

    1. **Fetch IDs and URLs**: Retrieves all job IDs and corresponding URLs from the database.
    2. **Validation and Logging**:
       - Checks if the URL is valid (non-empty and has a valid scheme like http or https).
       - Logs invalid or empty URLs as warnings.
    3. **Fallback Mechanism**:
       - For invalid URLs, attempts to construct and validate a fallback URL for the `jobup` platform.
       - Logs the result of the fallback URL validation.
    4. **SSL Error Handling**:
       - For URLs that raise an SSL certificate verification error, retries the request with SSL verification disabled (`verify=False`).
       - Logs both the occurrence of the SSL error and the result of the retry.
    5. **Error Handling**:
       - Handles and logs other request errors (e.g., timeouts, connection errors) that occur during URL validation.

    Logging Details:
    - **INFO**:
      - Logs valid URLs that successfully respond with status codes below 400.
      - Logs valid fallback URLs when the primary URL is invalid or empty.
    - **WARNING**:
      - Logs invalid URLs (status codes 400 or above).
      - Logs fallback URL failures.
      - Logs when retrying with `verify=False` for SSL errors.
    - **ERROR**:
      - Logs errors during URL validation, including SSL errors and general request exceptions.

    Parameters:
    ----------
    sqlite_path : str, optional
        The file path to the SQLite database containing the job postings. Defaults to the `jobs` database in `DATABASES`.

    Returns:
    -------
    list
        A list of job IDs corresponding to invalid or unreachable URLs.

    Example:
    -------
    >>> ids_to_delete = get_ids_to_delete()
    >>> print(ids_to_delete)
    ["job_id_1", "job_id_2", ...]
    """
    import time
    start_time = time.time()
    logging.info("[GET_IDS_TO_DELETE] Starting links check.")    
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Fetch all IDs and URLs from the database
    cursor.execute("SELECT id, externalUrl FROM jobs")
    ids_and_links = cursor.fetchall()
    conn.close()

    ids_to_delete = []

    for job_id, link in ids_and_links:
        try:
            # Skip invalid or empty URLs
            if not link or not urlparse(link).scheme:
                logging.warning(f"[GET_IDS_TO_DELETE] Invalid URL detected: ID={job_id}, URL='{link}'")
                
                # Try the fallback Jobup URL
                jobup_link = f"https://www.jobup.ch/en/jobs/detail/{job_id}/?source=vacancy_search"
                try:
                    response = requests.head(jobup_link, timeout=10)
                    if response.status_code < 400:
                        logging.info(f"[GET_IDS_TO_DELETE] Fallback link is valid: ID={job_id}, URL={jobup_link}")
                        continue  # Skip to the next job since the fallback worked
                    else:
                        logging.warning(f"[GET_IDS_TO_DELETE] Fallback link is invalid: ID={job_id}, URL={jobup_link}, Status Code={response.status_code}")
                        ids_to_delete.append(job_id)
                except requests.RequestException as e:
                    logging.error(f"[GET_IDS_TO_DELETE] Error checking fallback URL: ID={job_id}, URL={jobup_link}, Error={e}")
                    ids_to_delete.append(job_id)
                continue  # Move to the next job after handling the fallback

            # Check the original link with a HEAD request
            try:
                response = requests.head(link, timeout=10)
                if response.status_code < 400:
                    logging.info(f"[GET_IDS_TO_DELETE] Link is valid: ID={job_id}, URL={link}")
                else:
                    logging.warning(f"[GET_IDS_TO_DELETE] Invalid link: ID={job_id}, URL={link}, Status Code={response.status_code}")
                    ids_to_delete.append(job_id)

            except requests.exceptions.SSLError as ssl_error:
                logging.warning(f"[GET_IDS_TO_DELETE] SSL error for URL: {link}, attempting with verify=False. Error: {ssl_error}")
                try:
                    # Retry with SSL verification disabled
                    response = requests.head(link, timeout=10, verify=False)
                    if response.status_code < 400:
                        logging.info(f"[GET_IDS_TO_DELETE] Link is valid with verify=False: ID={job_id}, URL={link}")
                    else:
                        logging.warning(f"[GET_IDS_TO_DELETE] Invalid link even with verify=False: ID={job_id}, URL={link}, Status Code={response.status_code}")
                        ids_to_delete.append(job_id)
                except requests.RequestException as e:
                    logging.error(f"[GET_IDS_TO_DELETE] Error checking URL with verify=False: ID={job_id}, URL={link}, Error={e}")
                    ids_to_delete.append(job_id)

        except requests.RequestException as e:
            # Log the error and add the ID to the deletion list
            logging.error(f"[GET_IDS_TO_DELETE] Error checking original URL: ID={job_id}, URL={link}, Error={e}")
            ids_to_delete.append(job_id)

    elapsed_time = time.time() - start_time
    logging.info(f"[GET_IDS_TO_DELETE] Processed {len(ids_and_links)} records. Found {len(ids_to_delete)} invalid links.")
    logging.info(f"[GET_IDS_TO_DELETE] Ending links check. Duration: {elapsed_time:.2f} seconds.")
    
    return ids_to_delete


def clean_sqlite_database(sqlite_path=DATABASES['jobs'], ids_to_delete=[]):
    """
    Cleans the jobs database by identifying and deleting rows with invalid or unreachable URLs.

    This function performs the following steps:
    1. Calls `get_ids_to_delete` to get a list of IDs corresponding to invalid URLs.
    2. Deletes rows from the database with those IDs.
    3. Logs the operation status, including the number of rows deleted and any errors encountered.

    Logging Details:
    - **INFO**: Logs when the function starts and ends, and the number of rows deleted.
    - **WARNING**: Logs if there are no IDs to delete.
    - **ERROR**: Logs any exceptions encountered during the database operation.
    
    Parameters:
    ----------
    sqlite_path : str, optional
        The file path to the SQLite database containing the job postings. Defaults to the `jobs` database in `DATABASES`.
    
    """
    logging.info("[CLEAN_SQLITE_DATABASE] Starting database cleanup.")
    
    if not ids_to_delete:
        logging.info("[CLEAN_SQLITE_DATABASE] No IDs to delete. Skipping cleanup.")
        return
    
    conn = sqlite3.connect(DATABASES['jobs'])
    cursor = conn.cursor()

    try:
        placeholders = ','.join(['?'] * len(ids_to_delete))
        query = f"DELETE FROM jobs WHERE id IN ({placeholders})"
        cursor.execute(query, ids_to_delete)
        conn.commit()
        logging.info(f"[CLEAN_SQLITE_DATABASE] Deleted {cursor.rowcount} rows from the table.")
    except sqlite3.Error as e:
        logging.error(f"[CLEAN_SQLITE_DATABASE] An error occurred while deleting rows: {e}")
    finally:
        conn.close()
        logging.info("[CLEAN_SQLITE_DATABASE] Database cleanup complete.")

def clean_chroma_database(chroma_path=DATABASES['job_ads_embeddings'], ids_to_delete = []):
    """
    Deletes vector store entries one by one, logging success and failure.

    Parameters:
    ----------
    vector_store : Your vector store object
        The vector store from which to delete entries.
    ids : list[str]
        A list of IDs to delete.

    Returns:
    -------
    None
    """
    logging.info(f"[CLEAN_CHROMA_DATABASE] Chroma database cleanup started.")

    if not ids_to_delete:
        logging.info("[CLEAN_CHROMA_DATABASE] No IDs to delete. Skipping cleanup.")
        return
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma(
        collection_name="job_ads_embeddings",
        embedding_function=embeddings,
        persist_directory=chroma_path,
    )

    for id in ids_to_delete:
        try:
            vector_store.delete(id)
            logging.info(f"[CLEAN_CHROMA_DATABASE] Deleted Chroma ID: {id}")
        except Exception as e:
            logging.error(f"[CLEAN_CHROMA_DATABASE] Error deleting Chroma ID: {id}, Error: {e}")
    
    logging.info(f'[CLEAN_CHROMA_DATABASE] Deleted {len(ids_to_delete)} entries from the Chroma database.')
    logging.info(f"[CLEAN_CHROMA_DATABASE] Chroma database cleanup complete.")



def clean_databases(sqlite_path=DATABASES['jobs'], chroma_path=DATABASES['job_ads_embeddings']):
    """
    Cleans up both the SQLite and Chroma databases by removing invalid or unreachable job postings.

    This function performs the following steps:

    1. **Retrieve Invalid IDs**:
       - Calls `get_ids_to_delete` to identify job IDs with invalid or unreachable URLs from the SQLite database.
       - If no invalid IDs are found, logs an informational message and exits early.

    2. **SQLite Cleanup**:
       - Attempts to delete rows with invalid job IDs from the SQLite database using `clean_sqlite_database`.
       - Logs any errors encountered during the process.

    3. **Chroma Cleanup**:
       - Attempts to delete vector store entries for the invalid job IDs from the Chroma database using `clean_chroma_database`.
       - Logs any errors encountered during the process.

    4. **Error Handling**:
       - Each cleanup operation (SQLite and Chroma) is wrapped in a `try-except` block to ensure that one failure does not affect the other.
       - Logs detailed error messages if exceptions are raised.

    5. **Logging**:
       - Logs the start and end of the database cleanup process.
       - Provides granular logging for each step, including whether IDs were found, deleted, or if any operations failed.

    Parameters:
    ----------
    sqlite_path : str, optional
        The file path to the SQLite database containing job postings. Defaults to the `jobs` database defined in `DATABASES`.

    chroma_path : str, optional
        The file path to the Chroma database directory. Defaults to the `job_ads_embeddings` database defined in `DATABASES`.

    Returns:
    -------
    None

    Example:
    -------
    >>> clean_databases(sqlite_path='/path/to/jobs.db', chroma_path='/path/to/chroma_db')
    """
    logging.info(f"[CLEAN_DATABASES] Starting SQLITE and CHROMA Database cleanup.")

    ids_to_delete = get_ids_to_delete(sqlite_path)
    if not ids_to_delete:
        logging.info("[CLEAN_DATABASES] No IDs to delete. The database is already clean.")
        return

    try:
        clean_sqlite_database(sqlite_path, ids_to_delete)
    except Exception as e:
        logging.error(f"[CLEAN_DATABASES] SQLITE Database cleanup failed: {e}")

    try:
        clean_chroma_database(chroma_path, ids_to_delete)
    except Exception as e:
        logging.error(f"[CLEAN_DATABASES] CHROMA Database cleanup failed: {e}")

    logging.info(f"[CLEAN_DATABASES] SQLITE and CHROMA Database cleanup complete.")
