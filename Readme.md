# YourERPCoach — AI Resume Parser & Search

Lightweight Flask app to upload ERP consultant resumes, parse them with Google Gemini (Gemini API), store structured data in an Excel file, and perform natural-language candidate search.

## Features
- Upload PDF / Word resumes and parse with Gemini AI
- Store parsed data in `resumes_database.xlsx`
- Natural-language search over parsed resumes
- Download database and view basic stats
- Minimal UI: Home / Upload / Search pages in `templates/`

## Files
- Main app: [app.py](app.py)
- Dependencies: [requirements.txt](requirements.txt)
- Templates: [templates/Home.html](templates/Home.html), [templates/Resume.html](templates/Resume.html), [templates/Search.html](templates/Search.html)
- Uploads folder: `uploads/` (created automatically)

## Prerequisites
- Python 3.8+
- pip

## Install & Setup

1. Clone or copy repository to your machine.

2. (Recommended) Create & activate a virtual environment:
   - Linux/macOS:
     ```sh
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```ps1
     python -m venv venv
     venv\Scripts\Activate.ps1
     ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Enter your Gemini API key:
   - Open [app.py](app.py).
   - Replace the placeholder at line 17:
     ```py
     GEMINI_API_KEY = "Enter you Gemini Api Key here"
     ```
     with:
     ```py
     GEMINI_API_KEY = "your_actual_gemini_api_key_here"
     ```
   - Note: the app expects a valid Gemini key to call the API. If you prefer, you may modify the code to load the key from an environment variable.

5. (Optional) Verify uploads folder exists (app creates it automatically):
   ```sh
   ls uploads || mkdir uploads
   ```

## Run the app
Start the Flask app:
```sh
python app.py
```
Open http://127.0.0.1:5000/ in your browser.

## Endpoints / Usage
- GET `/` — Home page ([templates/Home.html](templates/Home.html))
- GET `/resume` — Upload page ([templates/Resume.html](templates/Resume.html))
- POST `/upload` — Upload resume (form field name: `resume`). Backend flow:
  - [`allowed_file`](app.py) validates file extension
  - [`extract_text_from_pdf`](app.py) or [`extract_text_from_docx`](app.py) extracts text
  - [`parse_resume_with_gemini`](app.py) calls Gemini to extract structured fields
  - [`save_to_excel`](app.py) appends parsed data to `resumes_database.xlsx`
- GET `/search` — Search UI ([templates/Search.html](templates/Search.html))
- POST `/search` — Search backend uses [`search_resumes_with_gemini`](app.py)
- GET `/download-database` — Download `resumes_database.xlsx`
- GET `/api/stats` — Get parsed resume count

## Troubleshooting
- Gemini not configured / no key: the app prints configuration errors and `model` will be `None`. Set `GEMINI_API_KEY` as described above.
- If parsing fails, logs are printed to console. Check the printed Gemini response snippet when JSON decode fails.
- Max upload size: 16 MB (`app.config['MAX_CONTENT_LENGTH']`). Adjust in [app.py](app.py) if needed.

## Notes & Internals
- Data stored in `resumes_database.xlsx` (`EXCEL_FILE` in [app.py](app.py)).
- The parser expects the Gemini response to be a JSON object exactly as specified in `parse_resume_with_gemini` prompt. You can find that function in [app.py](app.py).
- Search concatenates rows from the Excel file and asks Gemini to return matching resume indices and relevance scores (`search_resumes_with_gemini` in [app.py](app.py)).

## Development
- Change templates in `templates/` to update UI.
- Add better error handling, environment-based config, and secure key storage for production.

