import sqlite3
import requests
import gzip
import io
import xml.etree.ElementTree as ET
import time
import re
from bs4 import BeautifulSoup
from config.settings import DATABASES

def get_industries():    
    # Use a `with` statement for safe connection handling
    with sqlite3.connect(DATABASES["identifiers"], timeout=20) as conn:
        cursor = conn.cursor()

        # Create table with multi-column primary key
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS industries (
                id INTEGER,
                lang TEXT,
                name TEXT,
                PRIMARY KEY (id, lang)
            )
        ''')

        # Truncate the table to replace data
        #cursor.execute("DELETE FROM industries")
        #conn.commit()

        # Sitemap URL
        url = "https://www.jobup.ch/sitemaps/sitemap.industry.xml.gz"

        # Download and decompress the sitemap
        response = requests.get(url)
        if response.status_code == 200:
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
                sitemap_xml = f.read()

            # Parse the XML content
            root = ET.fromstring(sitemap_xml)
            namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Extract industry URLs
            industry_urls = [
                url_tag.find("ns:loc", namespace).text
                for url_tag in root.findall("ns:url", namespace)
                if "industry=" in url_tag.find("ns:loc", namespace).text
            ]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # Loop through the industry URLs and fetch their corresponding names
            for url in industry_urls:
                industry_id = url.split("industry=")[1].split("&")[0]  # Extract industry ID
                lang = "FR" if "/fr/" in url else "EN"  # Determine language from URL

                # Fetch the page content to extract the industry name
                time.sleep(5)  # Delay to avoid rate-limiting
                page_response = requests.get(url, headers=headers)
                if page_response.status_code == 200:
                    soup = BeautifulSoup(page_response.text, "html.parser")
                    title_tag = soup.find("title")
                    if title_tag:
                        # Extract industry name from the <title>
                        match = re.search(r'"(.*?)\"', title_tag.text)
                        if match:
                            industry_name = match.group(1)

                            # Insert the data into the SQLite database
                            try:
                                cursor.execute(
                                    "INSERT OR REPLACE INTO industries (id, lang, name) VALUES (?, ?, ?)",
                                    (industry_id, lang, industry_name)
                                )
                            except sqlite3.IntegrityError:
                                print(f"Duplicate entry for id={industry_id}, lang={lang}")
                else:
                    print(f"Failed to fetch industry page for ID {industry_id}: {page_response.status_code}")

            # Commit changes to the database
            conn.commit()


### Obsolete function. New fetch_industries moved to constants.py

# def fetch_industries(lang='EN') -> list:
#     """
#     fetches industries from the database

#     Args:
#     lang (str): language of the industries to fetch (EN or FR)

#     Returns:
#     list: list of industries in the table
#     """
    
#     conn = sqlite3.connect(DATABASES["identifiers"])
#     cursor = conn.cursor()
#     cursor.execute(f"SELECT id, name FROM industries where lang = '{lang}'")
#     industries = cursor.fetchall()
#     conn.close()
#     return industries