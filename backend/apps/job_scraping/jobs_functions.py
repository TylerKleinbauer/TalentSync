import requests
import json
import sqlite3
from bs4 import BeautifulSoup
import re
import time
import traceback
import xml.etree.ElementTree as ET
import pandas as pd
from config.settings import DATABASES
import logging
import json

def get_links(page_number, published_since):
    """
    Get the job links from a specific page number on Jobup.

    Args:
        page_number (int): The page number to fetch job links from.
        published_since (int): The number of days since the job was published.
    
    Returns:
        list: A list of job links on the specified page.
    """
    
    logging.info(f"[GET_LINKS] Starting to fetch job links for page {page_number} published since {published_since} days.")

    page_number_str = str(page_number)
    published_since_str = str(published_since)
    url = f"https://www.jobup.ch/en/jobs/?page={page_number_str}&publication-date={published_since_str}&region=33&region=34&region=40&region=42&region=52&region=57&term="
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as e:
        logging.error(f"[GET_LINKS] RequestException: Unable to fetch the page for page_number={page_number}. Error: {e}")
        return []
    
    if response.status_code == 200:
        logging.info(f"[GET_LINKS] Successfully fetched page {page_number} with status code 200.")
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            job_links = ["https://www.jobup.ch"+a["href"] for a in soup.select('a[data-cy="job-link"]')]
            logging.info(f"[GET_LINKS] Extracted {len(job_links)} job links from page {page_number}.")
            return job_links
        except Exception as e:
            logging.error(f"[GET_LINKS] Error parsing the HTML for page_number={page_number}. Error: {e}")
            return []
    else:
        logging.error(f"[GET_LINKS] Failed to fetch links from page {page_number}. Status code: {response.status_code}")
        return []
    
def get_job_info(link):
    """
    Extract job information from a Jobup job posting URL.

    Args:
        link (str): The URL of the Jobup job posting.

    Returns:
        dict | None: A dictionary containing the extracted job information,
                     or None if something went wrong.
    """
    logging.info(f"[GET_JOB_INFO] Starting job info extraction for link: {link}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        response = requests.get(link, headers=headers)
    except requests.RequestException as e:
        logging.error(f"[GET_JOB_INFO] RequestException: Unable to fetch the page for link={link}. Error: {e}")
        return None

    if response.status_code == 200:
        logging.info(f"[GET_JOB_INFO] Successfully fetched page with status code 200 for link: {link}")
        soup = BeautifulSoup(response.text, "html.parser")
        script_tags = soup.find_all("script")

        target_script = None
        # Look for the script containing __REACT_QUERY_STATE__
        for script in script_tags:
            # script.string can be None if it's an external script or has no direct text
            if script.string and "__REACT_QUERY_STATE__" in script.string:
                target_script = script.string
                logging.info("[GET_JOB_INFO] Found script containing __REACT_QUERY_STATE__.")
                break

        if not target_script:
            logging.warning("[GET_JOB_INFO] Script containing __REACT_QUERY_STATE__ not found in the HTML.")
            return None

        match = re.search(r"__REACT_QUERY_STATE__ = ({.*});", target_script)
        if not match:
            logging.warning("[GET_JOB_INFO] __REACT_QUERY_STATE__ object pattern not found in the script content.")
            return None

        script_content = match.group(1)
        # Replace occurrences of 'undefined' with 'null' to make it valid JSON
        script_content = re.sub(r"\bundefined\b", "null", script_content)

        try:
            react_query_state = json.loads(script_content)
            logging.info(f"[GET_JOB_INFO] Successfully parsed __REACT_QUERY_STATE__ for link: {link}")
            return react_query_state
        except json.JSONDecodeError as e:
            logging.error(f"[GET_JOB_INFO] JSONDecodeError: Failed to parse JSON after replacement for link={link}. Error: {e}")
            return None

    else:
        logging.error(f"[GET_JOB_INFO] Non-200 status code received. code={response.status_code}, link={link}")
        return None

def clean_json(raw_json, link):
    """
    Extract relevant fields from the raw JSON object and format them for insertion into SQLite.

    Args:
        raw_json (dict): Raw JSON object from web scraping.

    Returns:
        list of dict: A list of dictionaries, each containing the cleaned and formatted data.
    """
    logging.info(f"[CLEAN_JSON] Starting JSON cleaning process for link: {link}")
    
    cleaned_data = []
    queries = raw_json.get('queries', [])

    logging.debug(f"[CLEAN_JSON] Number of queries to process: {len(queries)}")

    for idx, query in enumerate(queries, start=1):
        state = query.get('state', {})
        data = state.get('data', {})

        if data:
            logging.debug(f"[CLEAN_JSON] Processing query {idx} with data for link: {link}")
            # Extract fields with safe handling for empty lists and dictionaries
            contacts = data.get('contacts', [{}])
            contact_firstName = contacts[0].get('firstName', '') if contacts else ''
            contact_lastName = contacts[0].get('lastName', '') if contacts else ''
            
            locations = data.get('locations', [{}])
            location_postalCode = locations[0].get('postalCode', '') if locations else ''
            location_city = locations[0].get('city', '') if locations else ''
            location_cantonCode = locations[0].get('cantonCode', '') if locations else ''
            location_countryCode = locations[0].get('countryCode', '') if locations else ''

            # Format list fields into comma-separated strings
            employment_grades = ", ".join(map(str, data.get('employmentGrades', [])))
            employment_position_ids = ", ".join(data.get('employmentPositionIds', []))
            employment_type_ids = ", ".join(data.get('employmentTypeIds', []))

            # Handle languageSkills (list of dictionaries)
            language_skills = data.get('languageSkills', [])
            formatted_language_skills = ", ".join(
                [f"{skill.get('language', '')} (Level {skill.get('level', '')})" for skill in language_skills]
            )

            # Clean and format the data
            cleaned_entry = {
                'id': data.get('id'),
                'externalUrl': data.get('applicationOptions', {}).get('externalUrl', ''),
                'logo': data.get('logo', ''),
                'company_id': data.get('company', {}).get('id', ''),
                'company_name': data.get('company', {}).get('name', ''),
                'contact_firstName': contact_firstName,
                'contact_lastName': contact_lastName,
                'headhunterApplicationAllowed': data.get('headhunterApplicationAllowed', False),
                'initialPublicationDate': data.get('initialPublicationDate', ''),
                'isActive': data.get('isActive', False),
                'isPaid': data.get('isPaid', False),
                'language_skills': formatted_language_skills,  # Formatted list of dictionaries
                'locations_postalCode': location_postalCode,
                'locations_city': location_city,
                'locations_cantonCode': location_cantonCode,
                'locations_countryCode': location_countryCode,
                'publicationDate': data.get('publicationDate', ''),
                'publicationEndDate': data.get('publicationEndDate', ''),
                'skills': ", ".join(data.get('skills', [])),  # Format list into a comma-separated string
                'synonym': data.get('synonym', ''),
                'template_lead': data.get('template', {}).get('lead', ''),
                'template_title': data.get('title', ''),
                'template_text': data.get('template', {}).get('text', ''),
                'industry': data.get('industry', ''),
                'regionID': data.get('regionId', ''),
                'employmentGrades': employment_grades,
                'employmentPositionIds': employment_position_ids,
                'employmentTypeIds': employment_type_ids
            }

            # Validate critical fields
            if not cleaned_entry['id']:
                logging.warning(f"[CLEAN_JSON] Missing 'id' in query {idx} for link: {link}. Entry will be skipped.")
                continue  # Skip entries without an ID

            # Log details about the cleaned entry (optional, can be verbose)
            logging.debug(f"[CLEAN_JSON] Cleaned entry for ID: {cleaned_entry['id']} with link: {link}")

            # Append the cleaned entry to the results
            cleaned_data.append(cleaned_entry)
        else:
            logging.warning(f"[CLEAN_JSON] No data found in query {idx} for link: {link}. Skipping.")

    logging.info(f"[CLEAN_JSON] Completed cleaning JSON for link: {link}. Total cleaned entries: {len(cleaned_data)}.")
    return cleaned_data

def insert_jobinfo_sqlite(clean_data, db_path=DATABASES['jobs']):
    """
    Inserts cleaned job data into a SQLite database, adding new columns dynamically if they don't exist.
    Removes HTML tags from template_lead and template_text and appends template_text to template_lead.

    Parameters:
        clean_data (list of dict): Cleaned job data where each entry is a dictionary containing field-value pairs.
        db_path (str): Path to the SQLite database file.
    """
    logging.info("[INSERT_JOBINFO_SQLITE] Starting insertion of cleaned job data into SQLite database.")
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()

    # Define the desired table schema
    table_schema = {
        'id': 'TEXT PRIMARY KEY',
        'externalUrl': 'TEXT',
        'logo': 'TEXT',
        'company_id': 'TEXT',
        'company_name': 'TEXT',
        'contact_firstName': 'TEXT',
        'contact_lastName': 'TEXT',
        'headhunterApplicationAllowed': 'BOOLEAN',
        'initialPublicationDate': 'TEXT',
        'isActive': 'BOOLEAN',
        'isPaid': 'BOOLEAN',
        'language_skills': 'TEXT',
        'postalCode': 'TEXT',
        'city': 'TEXT',
        'cantonCode': 'TEXT',
        'countryCode': 'TEXT',
        'publicationDate': 'TEXT',
        'publicationEndDate': 'TEXT',
        'skills': 'TEXT',
        'synonym': 'TEXT',
        'template_lead': 'TEXT',
        'template_title': 'TEXT',
        'industry': 'INTEGER',
        'regionID': 'INTEGER',
        'employmentPositionIds': 'INTEGER',
        'employmentTypeIds': 'INTEGER',
        'employmentGrades': 'TEXT'
    }

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            externalUrl TEXT,
            logo TEXT,
            company_id TEXT,
            company_name TEXT,
            contact_firstName TEXT,
            contact_lastName TEXT,
            headhunterApplicationAllowed BOOLEAN,
            initialPublicationDate TEXT,
            isActive BOOLEAN,
            isPaid BOOLEAN,
            language_skills TEXT,
            postalCode TEXT,
            city TEXT,
            cantonCode TEXT,
            countryCode TEXT,
            publicationDate TEXT,
            publicationEndDate TEXT,
            skills TEXT,
            synonym TEXT,
            template_lead TEXT,
            template_title TEXT,
            industry INTEGER,
            regionID INTEGER,
            employmentPositionIds INTEGER,
            employmentTypeIds INTEGER,
            employmentGrades TEXT
        )
    ''')

    # Check and add any missing columns dynamically
    cursor.execute("PRAGMA table_info(jobs)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    for column, column_type in table_schema.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column} {column_type}")
            logging.debug(f"[INSERT_JOBINFO_SQLITE] Added missing column '{column}' to 'jobs' table.")

    # Prepare the insert query dynamically based on the schema
    insert_query = f'''
        INSERT OR REPLACE INTO jobs ({', '.join(table_schema.keys())})
        VALUES ({', '.join(['?' for _ in table_schema])})
    '''

    # Insert data into the database
    for job in clean_data:
        job_id = job.get("id")
        if not job_id:
            logging.warning("[INSERT_JOBINFO_SQLITE] Skipping job entry without 'id'.")
            continue

        try:
            # Extract and clean `language_skills`
            language_skills_list = job.get("language_skills", [])
            language_skills_str = ", ".join(
                [
                    f"{skill.get('language', '')} (Level {skill.get('level', '')})"
                    for skill in language_skills_list if isinstance(skill, dict)
                ]
            )

            # Extract and clean `skills`
            skills_list = job.get("skills", [])
            skills_str = ", ".join(skills_list)

            # Clean and combine template fields
            template_lead_text = job.get("template_lead") or "" # Handle None values
            template_lead = BeautifulSoup(template_lead_text, "html.parser").get_text(strip=True)
            template_text_text = job.get("template_text") or "" # Handle None values
            template_text = BeautifulSoup(template_text_text, "html.parser").get_text(strip=True)

            combined_template = f"{template_lead}\n\n{template_text}".strip()

            # Convert table_schema.keys() to a list to allow indexing
            schema_keys = list(table_schema.keys())

            # Prepare data for insertion
            row_data = [
                job.get(column, None) for column in schema_keys
            ]
            row_data[schema_keys.index("language_skills")] = language_skills_str
            row_data[schema_keys.index("skills")] = skills_str
            row_data[schema_keys.index("template_lead")] = combined_template

            # Execute the insert
            cursor.execute(insert_query, row_data)
            logging.debug(f"[INSERT_JOBINFO_SQLITE] Inserted job ID: {job_id} into SQLite database.")
        except Exception as e:
            logging.error(f"[INSERT_JOBINFO_SQLITE] Error inserting job {job_id}: {e}")
            logging.debug(traceback.format_exc())

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    logging.info(f"[INSERT_JOBINFO_SQLITE] Inserted {len(clean_data)} job entries into SQLite database.")

def get_scraped_links():
    """
    Retrieve all previously scraped job links from the SQLite database.
    
    Returns:
        set: A set of job URLs that have already been scraped.
    """
    logging.info("[GET_SCRAPED_LINKS] Starting to fetch scraped links from SQLite database.")

    scraped_links = set()

    try:
        conn = sqlite3.connect(DATABASES['jobs'])
    except sqlite3.Error as e:
        logging.error(f"[GET_SCRAPED_LINKS] Failed to connect to SQLite database: {e}")
        return scraped_links  # Return empty set on failure
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs")
        id_list = [row[0] for row in cursor.fetchall()]
        logging.info(f"[GET_SCRAPED_LINKS] Retrieved {len(id_list)} job IDs from the database.")
    except sqlite3.Error as e:
        logging.error(f"[GET_SCRAPED_LINKS] Failed to execute SELECT query: {e}")
        conn.close()
        return scraped_links  # Return empty set on failure
    
    if not id_list:
        logging.warning("[GET_SCRAPED_LINKS] No job IDs found in the database.")   
    else:
        for job_id in id_list:
            if not job_id:
                logging.warning("[GET_SCRAPED_LINKS] Encountered a job entry with missing ID. Skipping.")
                continue  # Skip entries without a valid ID

            link = f"https://www.jobup.ch/en/jobs/detail/{job_id}/?source=vacancy_search"
            scraped_links.add(link)

        logging.info(f"[GET_SCRAPED_LINKS] Total scraped links collected: {len(scraped_links)}.")
    
    try:
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"[GET_SCRAPED_LINKS] Failed to close SQLite connection: {e}")

    logging.info("[GET_SCRAPED_LINKS] Completed fetching scraped links.")
    return scraped_links    

def scrape_and_store_jobs(max_pages=100, published_since=1, db_path=DATABASES['jobs']):
    """
    Scrape job postings from Jobup and insert them into an SQLite database.
    
    Args:
        max_pages (int): Maximum number of pages to scrape.
        db_path (str): Path to the SQLite database.
    """
    logging.info("[SCRAPE_AND_STORE_JOBS] Starting job scraping process.")
    
    scraped_links = get_scraped_links()  # Track already-scraped links

    for page_number in range(1, max_pages + 1):
        try:
            logging.info(f"[SCRAPE_AND_STORE_JOBS] Scraping page {page_number}...")
            
            # Get job links for the current page
            job_links = get_links(page_number, published_since)
            
            # Check if the current page redirects or repeats
            if not job_links or scraped_links.issuperset(job_links):
                logging.info("[SCRAPE_AND_STORE_JOBS] No new links found or redirection detected. Exiting loop.")
                break
            
            for link in job_links:
                if link in scraped_links:
                    logging.info(f"[SCRAPE_AND_STORE_JOBS] Skipping already-scraped link: {link}")
                    continue
                
                try:
                    # Fetch and clean job info
                    raw_info = get_job_info(link)
                    if not raw_info:
                        logging.warning(f"[SCRAPE_AND_STORE_JOBS] No job info found for {link}. Skipping.")
                        continue
                    clean_info = clean_json(raw_info, link)

                    if not clean_info:
                        logging.warning(f"[SCRAPE_AND_STORE_JOBS] Cleaned data is empty for link: {link}. Skipping insertion.")
                        continue
                    
                    # Insert into SQLite
                    insert_jobinfo_sqlite(clean_info, db_path)
                    scraped_links.add(link)  # Mark as scraped
                    logging.info(f"[SCRAPE_AND_STORE_JOBS] Successfully inserted job from {link} into database.")
                
                except Exception as e:
                    logging.error(f"[SCRAPE_AND_STORE_JOBS] Error processing job link {link}: {e}")
                    logging.debug(traceback.format_exc())
            
            # Respectful scraping
            time.sleep(5)
        
        except Exception as e:
            logging.error(f"[SCRAPE_AND_STORE_JOBS] Error on page {page_number}: {e}")
            logging.debug(traceback.format_exc())
            continue

    logging.info("[SCRAPE_AND_STORE_JOBS] Scraping completed.")

