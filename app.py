from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import PyPDF2
import docx
import json
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc'}

GEMINI_API_KEY = "Enter you Gemini Api Key here"
if GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
    print("⚠️ WARNING: Please set your GEMINI_API_KEY!")
    print("Get your key from: https://makersuite.google.com/app/apikey")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
    model = None

EXCEL_FILE = 'resumes_database.xlsx'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_path):
    """Extract text from Word document"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        raise Exception(f"Failed to extract text from Word document: {str(e)}")

def parse_resume_with_gemini(resume_text):
    """Parse resume using Gemini API"""
    if model is None:
        raise Exception("Gemini API is not configured. Please set your API key.")
    
    if not resume_text or len(resume_text) < 50:
        raise Exception("Resume text is too short or empty. Please check the file.")
    
    prompt = f"""
Extract the following information from this ERP Consultant resume and return ONLY a valid JSON object with no additional text:
{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "summary": "",
  "total_years_experience": "",
  "current_role": "",
  "current_company": "",
  "erp_systems": [],
  "erp_modules": [],
  "experience": [
    {{
      "company": "",
      "role": "",
      "duration": "",
      "responsibilities": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "university": "",
      "year": ""
    }}
  ],
  "technical_skills": [],
  "certifications": [],
  "projects": []
}}

Important:
- For erp_systems, extract systems like SAP, Oracle, Microsoft Dynamics, NetSuite, etc.
- For erp_modules, extract modules like FI, CO, MM, SD, PP, HR, CRM, SCM, etc.
- Return ONLY the JSON object, no markdown formatting or additional text.
- If information is not found, use empty string "" or empty array []

Resume text:
\"\"\"
{resume_text[:4000]}
\"\"\"
"""
    
    try:
        print("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise Exception("Empty response from Gemini API")
        
        result_text = response.text.strip()
        print(f"Gemini response received: {result_text[:200]}...")
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        elif result_text.startswith('```'):
            result_text = result_text[3:]
        
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        result_text = result_text.strip()
        
        parsed_data = json.loads(result_text)
        print("✅ Resume parsed successfully")
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {result_text if 'result_text' in locals() else 'No response'}")
        raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
    except Exception as e:
        print(f"Error in parse_resume_with_gemini: {str(e)}")
        raise Exception(f"Gemini API error: {str(e)}")

def save_to_excel(parsed_data):
    """Save parsed resume data to Excel"""
    try:
        flat_data = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Name': parsed_data.get('name', ''),
            'Email': parsed_data.get('email', ''),
            'Phone': parsed_data.get('phone', ''),
            'Location': parsed_data.get('location', ''),
            'LinkedIn': parsed_data.get('linkedin', ''),
            'Summary': parsed_data.get('summary', ''),
            'Total_Years_Experience': parsed_data.get('total_years_experience', ''),
            'Current_Role': parsed_data.get('current_role', ''),
            'Current_Company': parsed_data.get('current_company', ''),
            'ERP_Systems': ', '.join(parsed_data.get('erp_systems', [])),
            'ERP_Modules': ', '.join(parsed_data.get('erp_modules', [])),
            'Technical_Skills': ', '.join(parsed_data.get('technical_skills', [])),
            'Certifications': ', '.join(parsed_data.get('certifications', [])),
            'Education': json.dumps(parsed_data.get('education', [])),
            'Experience': json.dumps(parsed_data.get('experience', [])),
            'Projects': json.dumps(parsed_data.get('projects', []))
        }
        
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df = pd.concat([df, pd.DataFrame([flat_data])], ignore_index=True)
        else:
            df = pd.DataFrame([flat_data])
        
        df.to_excel(EXCEL_FILE, index=False)
        print(f"✅ Data saved to {EXCEL_FILE}")
        return True
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        raise Exception(f"Failed to save data to Excel: {str(e)}")

def search_resumes_with_gemini(search_query):
    """Search resumes using Gemini API"""
    if model is None:
        raise Exception("Gemini API is not configured. Please set your API key.")
    
    if not os.path.exists(EXCEL_FILE):
        return []
    
    df = pd.read_excel(EXCEL_FILE)
    
    resumes_text = ""
    for idx, row in df.iterrows():
        resumes_text += f"\n\n--- Resume {idx + 1} ---\n"
        resumes_text += f"Name: {row['Name']}\n"
        resumes_text += f"Email: {row['Email']}\n"
        resumes_text += f"Current Role: {row['Current_Role']}\n"
        resumes_text += f"ERP Systems: {row['ERP_Systems']}\n"
        resumes_text += f"ERP Modules: {row['ERP_Modules']}\n"
        resumes_text += f"Skills: {row['Technical_Skills']}\n"
        resumes_text += f"Experience: {row['Total_Years_Experience']}\n"
    
    prompt = f"""
Based on the following resumes database, find candidates that match this search query: "{search_query}"
Return a JSON array of matching resume indices (1-based) with relevance scores and reasons.
Format:
[
  {{"resume_number": 1, "relevance_score": 95, "reason": "Strong match because..."}},
  {{"resume_number": 2, "relevance_score": 80, "reason": "Good match because..."}}
]
Return ONLY the JSON array, no additional text. Sort by relevance score descending.

Resumes Database:
{resumes_text[:3000]}
"""
    
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        
        matches = json.loads(result_text.strip())
        
        results = []
        for match in matches:
            idx = match['resume_number'] - 1
            if 0 <= idx < len(df):
                resume_data = df.iloc[idx].to_dict()
                resume_data['relevance_score'] = match['relevance_score']
                resume_data['match_reason'] = match['reason']
                results.append(resume_data)
        
        return results
    except Exception as e:
        print(f"Error searching with Gemini: {str(e)}")
        raise Exception(f"Search failed: {str(e)}")

@app.route('/')
def home():
    """Home page route"""
    return render_template('Home.html')

@app.route('/resume')
def resume():
    """Resume upload page route"""
    return render_template('Resume.html')

@app.route('/search')
def search_page():
    """Search page route"""
    return render_template('Search.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and parsing"""
    try:
        if 'resume' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only PDF and Word documents allowed'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"File saved: {filepath}")
        
        try:
            if filename.lower().endswith('.pdf'):
                resume_text = extract_text_from_pdf(filepath)
            else:
                resume_text = extract_text_from_docx(filepath)
            
            print(f"Extracted text length: {len(resume_text)} characters")
            
            if not resume_text or len(resume_text) < 50:
                raise Exception("Could not extract text from file. The file might be empty or corrupted.")
            
        except Exception as e:
            os.remove(filepath)
            return jsonify({'success': False, 'error': f'Text extraction failed: {str(e)}'}), 500
        
        try:
            parsed_data = parse_resume_with_gemini(resume_text)
            
            if not parsed_data:
                raise Exception('Failed to parse resume - no data returned')
            
        except Exception as e:
            os.remove(filepath)
            return jsonify({'success': False, 'error': f'Resume parsing failed: {str(e)}'}), 500
        
        try:
            save_to_excel(parsed_data)
        except Exception as e:
            os.remove(filepath)
            return jsonify({'success': False, 'error': f'Database save failed: {str(e)}'}), 500
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Resume parsed and saved successfully',
            'data': parsed_data
        })
    
    except Exception as e:
        print(f"Unexpected error in upload_resume: {str(e)}")
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/search', methods=['POST'])
def search():
    """Handle resume search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        results = search_resumes_with_gemini(query)
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download-database')
def download_database():
    """Download the Excel database"""
    if os.path.exists(EXCEL_FILE):
        return send_file(EXCEL_FILE, as_attachment=True)
    return jsonify({'error': 'No database found'}), 404

@app.route('/api/stats')
def get_stats():
    """Get statistics about parsed resumes"""
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            return jsonify({
                'success': True,
                'count': len(df)
            })
        return jsonify({
            'success': True,
            'count': 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'count': 0,
            'error': str(e)
        })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 YourERPCoach Resume Parser Starting...")
    print("="*50)
    if GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
        print("⚠️  WARNING: GEMINI_API_KEY not set!")
        print("📝 Get your API key from: https://makersuite.google.com/app/apikey")
        print("💡 Set it as environment variable or in code")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)