import os


UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

EXCEL_FILE = 'resumes_database.xlsx'
LOCAL_DOCS_DIR = 'docs_for_rag'

SKYQ_BASE_URL = "https://ai.skyq.tech"

SKYQ_JWT_TOKEN = os.getenv("SKYQ_JWT_TOKEN") 

SKYQ_HEADERS = {
    "Authorization": f"Bearer {SKYQ_JWT_TOKEN}",
    "Content-Type": "application/json"
}

USE_BETA_ENVIRONMENT = True

YECC_API_TOKEN = os.getenv("YECC_API_TOKEN") 

if USE_BETA_ENVIRONMENT:
    YECC_BASE_URL = "https://api.yecc.tech"
    FRONTEND_ORIGIN = "https://beta.yecc.tech"
else:
    YECC_BASE_URL = "https://api.yecc.tech"
    FRONTEND_ORIGIN = "https://yecc.tech"

YECC_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"{YECC_API_TOKEN}",
    "Content-Type": "application/json",
    "Origin": FRONTEND_ORIGIN,
    "Referer": f"{FRONTEND_ORIGIN}/"
}

MODEL_CONFIGS = [
    {"model": "llama3:8b", "temperature": 0.1, "max_tokens": 1500},
    {"model": "llama3.2:3b", "temperature": 0.1, "max_tokens": 1500},
    {"model": "deepseek-r1:8b", "temperature": 0.1, "max_tokens": 1500},
    {"model": "gpt-oss:20b", "temperature": 0.1, "max_tokens": 1500},
]

MAX_TEXT_LENGTHS = [5000, 4000, 3000, 2500]

