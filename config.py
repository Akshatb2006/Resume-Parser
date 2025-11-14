import os

UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

EXCEL_FILE = 'resumes_database.xlsx'
LOCAL_DOCS_DIR = 'docs_for_rag'

SKYQ_BASE_URL = "https://ai.skyq.tech"

SKYQ_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImQ5NTIzM2VhLTYxY2ItNDY1NC05MGI4LTFkNjRhZGI0ZjE0YiJ9.bBlFzDMgLkNNim-8jGBXBeIkBNYC9HBqEvPPkgjRv3Q"  

SKYQ_HEADERS = {
    "Authorization": f"Bearer {SKYQ_JWT_TOKEN}",
    "Content-Type": "application/json"
}

USE_BETA_ENVIRONMENT = False

YECC_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NjMwMjM2ODcsIm5iZiI6MTc2MzAyMzY4NywiZXhwIjoxNzYzMjgyODg3LCJ1c2VySW5mbyI6eyJJRCI6Ik1qaz0iLCJSb2xlSUQiOiJBZG1pbiIsIkZpcnN0TmFtZSI6IlNhdXJhYmgiLCJMYXN0TmFtZSI6IkthcnZlIiwiUmVzdW1lVXJsIjoiIiwiQWNjZXNzQ29udHJvbCI6Int9IiwiRG9tYWluIjpudWxsLCJEZXNpZ25hdGlvbiI6bnVsbCwiVW5pcXVlRGV2aWNlSUQiOjgsInByb2ZpbGVJbWFnZSI6IlwvaW1nXC9wcm9maWxlXC9iaXMtbWFuLnBuZyJ9LCJsb2dpbk1ldGhvZCI6Im1vYmlsZSJ9.2Mv6FRuX0lN8yGVZBoqAaUZNFP1heb1rOOYqGsuxfC4"  

if USE_BETA_ENVIRONMENT:
    YECC_BASE_URL = "https://betaapi.yecc.tech"
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

