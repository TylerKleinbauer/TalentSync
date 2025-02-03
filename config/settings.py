import os
import sys
from langchain_openai import ChatOpenAI

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database paths
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Logging paths
LOGGING_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGGING_DIR, exist_ok=True)  # Ensure logs directory exists

# Database Names
DATABASES = {
    "identifiers": os.path.join(DATA_DIR, "identifiers.db"),
    "jobs": os.path.join(DATA_DIR, "jobs.db"),
    'employement_position_id': os.path.join(DATA_DIR, 'employement_position_id.db'),
    'job_ads_embeddings': DATA_DIR
}

# Logging configuration
LOGGING_LEVEL = "DEBUG"  # You can adjust this to INFO, WARNING, ERROR, or CRITICAL
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Log file paths
LOGGING_FILES = {
    "info": os.path.join(LOGGING_DIR, "info.log"),
    "error": os.path.join(LOGGING_DIR, "error.log"),
}

# Add project root to PYTHONPATH
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
