import json
import time
import requests
import re
from config import SKYQ_BASE_URL, SKYQ_HEADERS, MODEL_CONFIGS, MAX_TEXT_LENGTHS
from utils import clean_array, extract_email, extract_phone, extract_linkedin, extract_years_experience

def fix_json_string(json_str):
    """Fix common JSON formatting issues"""
    if not json_str or not json_str.strip():
        return "{}"
    
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*', '', json_str)
    
    json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL)
    json_str = re.sub(r'<thinking>.*?</thinking>', '', json_str, flags=re.DOTALL)
    
    json_str = json_str.strip()
    
    if not json_str:
        return "{}"
    
    start = json_str.find('{')
    end = json_str.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        return "{}"
    
    json_str = json_str[start:end+1]
    
    return json_str

def safe_json_parse(content, max_attempts=4):
    
    if not content or not content.strip():
        raise json.JSONDecodeError("Empty content", "", 0)
    
    for attempt in range(max_attempts):
        try:
            if attempt == 0:
                return json.loads(content)
            
            elif attempt == 1:
                fixed = fix_json_string(content)
                if fixed == "{}":
                    raise json.JSONDecodeError("No JSON found", content, 0)
                return json.loads(fixed)
            
            elif attempt == 2:
                fixed = fix_json_string(content)
                if fixed == "{}":
                    raise json.JSONDecodeError("No JSON found", content, 0)
                    
                open_braces = fixed.count('{')
                close_braces = fixed.count('}')
                open_brackets = fixed.count('[')
                close_brackets = fixed.count(']')
                
                if open_braces > close_braces:
                    fixed += '}' * (open_braces - close_braces)
                if open_brackets > close_brackets:
                    fixed += ']' * (open_brackets - close_brackets)
                
                return json.loads(fixed)
            
            else:
                fixed = fix_json_string(content)
                for i in range(len(fixed), 100, -100):
                    try:
                        test = fixed[:i].rstrip()
                        if test.endswith('}'):
                            result = json.loads(test)
                            print(f"      ⚠️  Recovered partial JSON ({i}/{len(fixed)} chars)")
                            return result
                    except:
                        continue
                        
        except json.JSONDecodeError as e:
            if attempt == max_attempts - 1:
                print(f"      JSON Error: {str(e)[:100]}")
                if hasattr(e, 'pos') and e.pos:
                    snippet_start = max(0, e.pos - 50)
                    snippet_end = min(len(content), e.pos + 50)
                    print(f"      Context: ...{content[snippet_start:snippet_end]}...")
                else:
                    print(f"      Content preview: {content[:200]}...")
                raise
            continue
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            continue
    
    raise json.JSONDecodeError("Could not parse JSON after all attempts", content, 0)

def smart_truncate_resume(resume_text, max_length=8000):
    """Smart truncation keeping important sections"""
    if len(resume_text) <= max_length:
        return resume_text, False
    
    header_size = min(2500, max_length // 3)
    footer_size = max_length - header_size - 50  
    
    header = resume_text[:header_size]
    footer = resume_text[-footer_size:]
    
    truncated = header + "\n\n[... middle section omitted ...]\n\n" + footer
    
    print(f"⚠️  Smart truncation applied:")
    print(f"   Original: {len(resume_text):,} chars")
    print(f"   Kept: {len(truncated):,} chars ({int(len(truncated)/len(resume_text)*100)}%)")
    
    return truncated, True

def create_original_prompt(resume_text):
    resume_snippet = resume_text[:7500] if len(resume_text) > 7500 else resume_text
    
    return f"""Extract information from this ERP Consultant resume. Return ONLY valid JSON (no markdown, no explanations, no thinking process).
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
  "technical_skills": [],
  "certifications": [],
  "education": [
    {{
      "degree": "",
      "university": "",
      "year": ""
    }}
  ],
  "job_experience": [
    {{
      "position": "",
      "country": "",
      "company_name": "",
      "employment_type": "",
      "currently_working_here": false,
      "from_date": "",
      "to_date": "",
      "short_description": ""
    }}
  ],
  "erp_projects_experience": [
    {{
      "company_name": "",
      "project_name": "",
      "project_domain": "",
      "project_type": [],
      "currently_working_on_this_project": false,
      "from_date": "",
      "to_date": "",
      "project_phases_involved": [],
      "work_location_type": [],
      "product": "",
      "track": "",
      "financials_modules": [],
      "hcm_modules": [],
      "scm_modules": [],
      "role": ""
    }}
  ]
}}

EXTRACTION RULES (STRICT & ROBUST):
A. GENERAL RULES
1. If a field is not found, return "" or [] (never guess or hallucinate).
2. All extracted values must come directly from the resume text.
3. Maintain stable JSON structure even if resume is poorly formatted.
4. Do NOT invent companies, roles, modules, or degrees.
5. The output must be valid JSON only - no explanations, no markdown, no thinking process.

B. NAME EXTRACTION (VERY IMPORTANT)
1. If the resume does NOT explicitly say "Name", infer the name using:
   - The first bold/large text at the top
   - The first standalone line before contact info
   - The email prefix if needed (take first part before @)
   - Capitalized phrases that resemble human names
2. Ignore company names, project names, department names.
3. If multiple candidates appear, choose the primary one at the top.

C. PHONE EXTRACTION
1. Accept ALL formats: +91 9876543210, 9876543210, (987) 654-3210, 987.654.3210
2. Extract only numeric phone, last 10-12 digits.
3. If multiple numbers, pick the first valid mobile-like number.

D. EMAIL EXTRACTION
1. Extract any valid email with "@".
2. If multiple exist, pick the most personal-looking one.

E. LOCATION EXTRACTION
1. Look for city/state/country keywords anywhere.
2. Pick the FIRST location near contact section.

F. LINKEDIN EXTRACTION
1. Extract ANY linkedin.com URL.
2. Accept both http and https.

G. SUMMARY EXTRACTION
1. Look for "Summary", "Professional Summary", "Objective", "Profile".
2. If not found, capture the first 2-4 lines before experience starts.
3. Must be ≤ 3 sentences.

H. JOB EXPERIENCE EXTRACTION
1. Extract each job with: title, company, dates, location, responsibilities
2. Accept date formats: Jan 2020 – Mar 2023, 01/2020 to 03/2023, 2020-2023, 2021-Present
3. currently_working_here = true IF: "Present", "Now", "Till date", no end date
4.Look for keywords: "Responsibilities", "Duties", "Achievements", "Role", "Internships"

I. PROJECT EXTRACTION (ERP SPECIFIC)
1. For each project: name, region, modules, role, description
2. If multiple projects under one job → create multiple entries.

J. ERP MODULE DETECTION (AUTO-INFER)
Detect ALL module keywords: GL, AP, AR, FA, CM, INV, PO, OM, OTL, Payroll, etc.

K. ERP SYSTEM DETECTION
Detect: Oracle Fusion/Cloud, SAP, S/4HANA, NetSuite, Dynamics 365, Workday

L. EDUCATION, SKILLS, CERTIFICATIONS
Extract all degrees, technical skills, and certifications found.

Resume:
{resume_snippet}

Return ONLY the JSON object with no additional text:"""

def parse_single_chunk(chunk_text, chunk_description, model_config, timeout=150):
    """Parse with improved error handling and longer timeout"""
    
    prompt = create_original_prompt(chunk_text)
    
    payload = {
        "model": model_config["model"],
        "messages": [
            {
                "role": "system", 
                "content": "You are a resume parser. Return ONLY valid JSON with no additional text, no markdown, no explanations."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "stream": False,
        "temperature": 0.1,
        "max_tokens": model_config.get("max_tokens", 4000),
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            f"{SKYQ_BASE_URL}/api/chat/completions",
            headers=SKYQ_HEADERS,
            json=payload,
            timeout=timeout
        )

        if response.status_code == 500:
            raise Exception(f"Ollama server error (500) - model may be overloaded or crashed")
        elif response.status_code == 404:
            raise Exception(f"Model not found (404) - check if {model_config['model']} is installed")
        elif response.status_code == 429:
            raise Exception(f"Rate limit (429) - too many requests")
        elif response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text[:200]}")
        
        result = response.json()

        content = (
            result.get('choices', [{}])[0].get('message', {}).get('content') or 
            result.get('response', '') or
            result.get('content', '')
        )
        
        if not content or not content.strip():
            raise Exception("Empty response from API - model returned no content")
        
        parsed = safe_json_parse(content)
        
        if not isinstance(parsed, dict):
            raise Exception(f"Expected dict, got {type(parsed).__name__}")
        
        has_basic_data = any([
            parsed.get('name'),
            parsed.get('email'),
            parsed.get('phone'),
            parsed.get('erp_systems'),
            parsed.get('job_experience')
        ])
        
        if not has_basic_data:
            raise Exception("Parsed JSON has no useful data - all fields empty")
        
        return parsed
        
    except requests.exceptions.Timeout:
        raise Exception(f"Request timeout after {timeout}s - model too slow")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Connection error - is Ollama running?")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)[:100]}")
    except Exception as e:
        # Re-raise with context
        error_type = type(e).__name__
        error_msg = str(e)[:200]
        raise Exception(f"{error_type}: {error_msg}")

def parse_with_single_pass(resume_text, max_length, retry_count):
    """Parse resume with all available models"""
    
    errors = []
    best_result = None
    best_score = 0
    
    for idx, config in enumerate(MODEL_CONFIGS):
        try:
            print(f"🤖 Model {idx+1}/{len(MODEL_CONFIGS)}: {config['model']}")
            
            result = parse_single_chunk(resume_text[:max_length], "complete", config)
            
            score = score_resume_completeness(result)
            print(f"   ✅ Success! Completeness: {score}/100\n")
            
            if score > best_score:
                best_result = result
                best_score = score
            
            if score >= 60:
                return result
            
        except Exception as e:
            error_msg = str(e)[:200]
            errors.append(f"{config['model']}: {error_msg}")
            print(f"   ❌ Failed: {error_msg}\n")
            
            if "500" in error_msg or "crashed" in error_msg.lower():
                print(f"   ⏳ Waiting 5s for Ollama to recover...")
                time.sleep(5)
            else:
                time.sleep(2)
    
    if best_result and best_score > 0:
        print(f"✅ Returning best result (score: {best_score}/100)\n")
        return best_result
    
    if retry_count < 3:
        print(f"⚠️  All {len(MODEL_CONFIGS)} models failed:")
        for err in errors:
            print(f"   - {err}")
        print(f"\n⚠️  Retrying with smaller chunk size...\n")
        time.sleep(3)
        return parse_resume_with_skyq(resume_text, "Retry", retry_count + 1)
    
    raise Exception(f"All attempts failed after {retry_count+1} tries. Last errors: {errors[-2:]}")

def parse_resume_with_skyq(resume_text, candidate_name="Unknown", retry_count=0):
    """Main parsing function"""
    
    print(f"\n{'='*70}")
    print(f"📄 Parsing Resume - Attempt {retry_count + 1}/4")
    print(f"{'='*70}")
    print(f"Candidate: {candidate_name}")
    print(f"Resume length: {len(resume_text):,} characters")
    
    max_lengths = [7000, 5000, 3500, 2500]
    max_length = max_lengths[min(retry_count, len(max_lengths)-1)]
    
    print(f"Max chunk size: {max_length:,} characters")
    print(f"{'='*70}\n")
    
    if len(resume_text) > max_length:
        print(f"⚠️  Resume too long, applying smart truncation\n")
        resume_text, was_truncated = smart_truncate_resume(resume_text, max_length)
    
    return parse_with_single_pass(resume_text, max_length, retry_count)

def enhance_parsed_data(parsed_data, resume_text):
    
    for field in ['erp_systems', 'erp_modules', 'technical_skills', 'certifications']:
        if field in parsed_data:
            parsed_data[field] = clean_array(parsed_data[field])
    
    if not parsed_data.get('email'):
        email = extract_email(resume_text)
        if email:
            parsed_data['email'] = email
    
    if not parsed_data.get('phone'):
        phone = extract_phone(resume_text)
        if phone:
            parsed_data['phone'] = phone
    
    if not parsed_data.get('linkedin'):
        linkedin = extract_linkedin(resume_text)
        if linkedin:
            parsed_data['linkedin'] = linkedin
    
    erp_mappings = {
        'D365': 'Microsoft Dynamics 365',
        'EBS': 'Oracle E-Business Suite',
        'JDE': 'JD Edwards',
        'PS': 'PeopleSoft',
        'Netsuite': 'NetSuite',
        'Ms Dynamics': 'Microsoft Dynamics',
        'Oracle Cloud': 'Oracle Cloud ERP',
        'Fusion': 'Oracle Fusion'
    }
    
    normalized_erp = []
    for erp in parsed_data.get('erp_systems', []):
        normalized = erp_mappings.get(erp, erp)
        if normalized not in normalized_erp:
            normalized_erp.append(normalized)
    parsed_data['erp_systems'] = normalized_erp
    
    if not parsed_data.get('total_years_experience'):
        years = extract_years_experience(resume_text)
        if years:
            parsed_data['total_years_experience'] = str(years)
    
    for field in ['technical_skills', 'certifications', 'erp_systems', 'erp_modules']:
        if not parsed_data.get(field):
            parsed_data[field] = []
    
    return parsed_data

def score_resume_completeness(parsed_data):
    """Score completeness (0-100)"""
    score = 0
    
    if parsed_data.get('name'): score += 5
    if parsed_data.get('email'): score += 5
    if parsed_data.get('phone'): score += 5
    if parsed_data.get('location'): score += 5
    if parsed_data.get('summary'): score += 5
    if parsed_data.get('total_years_experience'): score += 5
    
    if parsed_data.get('erp_systems'): score += 15
    if parsed_data.get('erp_modules'): score += 15
    
    if parsed_data.get('job_experience') and len(parsed_data['job_experience']) > 0: 
        score += 10
    if parsed_data.get('erp_projects_experience') and len(parsed_data['erp_projects_experience']) > 0:
        score += 10
    
    if parsed_data.get('current_role'): score += 3
    if parsed_data.get('current_company'): score += 2
    
    if parsed_data.get('education'): score += 5
    if parsed_data.get('technical_skills'): score += 5
    if parsed_data.get('certifications'): score += 5
    
    return min(score, 100)

def deduplicate_items(items, key_fields):
    """Remove duplicates"""
    seen = set()
    unique = []
    
    for item in items:
        if not isinstance(item, dict):
            if item not in seen:
                seen.add(item)
                unique.append(item)
            continue
        
        key = tuple(str(item.get(f, '')).lower().strip() for f in key_fields)
        if key not in seen and any(key):
            seen.add(key)
            unique.append(item)
    
    return unique

def merge_parsed_chunks(chunks_results):
    """Merge multiple chunk results"""
    if not chunks_results:
        return {}
    if len(chunks_results) == 1:
        return chunks_results[0]
    
    merged = chunks_results[0].copy()
    
    for result in chunks_results[1:]:
        for field in ['name', 'email', 'phone', 'location', 'linkedin', 'summary', 
                      'total_years_experience', 'current_role', 'current_company']:
            if not merged.get(field) and result.get(field):
                merged[field] = result[field]
            elif result.get(field) and len(str(result[field])) > len(str(merged.get(field, ''))):
                merged[field] = result[field]
        
        for field in ['erp_systems', 'erp_modules', 'technical_skills', 'certifications']:
            if field in result:
                merged[field] = list(set(merged.get(field, []) + result[field]))
        
        if 'education' in result:
            merged['education'] = deduplicate_items(
                merged.get('education', []) + result['education'], 
                ['degree', 'university']
            )
        
        if 'job_experience' in result:
            merged['job_experience'] = deduplicate_items(
                merged.get('job_experience', []) + result['job_experience'],
                ['company_name', 'position']
            )
        
        if 'erp_projects_experience' in result:
            merged['erp_projects_experience'] = deduplicate_items(
                merged.get('erp_projects_experience', []) + result['erp_projects_experience'],
                ['project_name']
            )
    
    return merged