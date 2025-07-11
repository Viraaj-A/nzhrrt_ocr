import os
import json
from google import genai
from google.genai import types
import pathlib
from spire.doc import *
from spire.doc.common import *
from dotenv import load_dotenv

load_dotenv()


def convert_rtf_to_pdf(rtf_file_path, output_dir):
    """Convert RTF file to PDF using Spire.Doc"""
    try:
        rtf_name = pathlib.Path(rtf_file_path).stem
        pdf_path = os.path.join(output_dir, f"{rtf_name}.pdf")
        
        doc = Document()
        doc.LoadFromFile(rtf_file_path)
        doc.SaveToFile(pdf_path, FileFormat.PDF)
        doc.Close()
        
        return pdf_path
    except Exception as e:
        print(f"Error converting RTF to PDF: {e}")
        return None


def process_pdf_with_gemini(pdf_path):
    """Process PDF with Gemini API to extract structured data"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    with open("legal_case_schema.json", "r") as f:
        schema = json.load(f)
    
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": schema
    }
    
    prompt = """
        You are a legal document extraction specialist. Analyze this legal document and extract ALL information into a JSON structure following the exact schema provided.

        CRITICAL REQUIREMENTS:

        1. DOCUMENT ANALYSIS FIRST:
        - Determine if this contains 1 or multiple cases
        - Identify page ranges for each case
        - Set document_metadata.total_cases and document_type accordingly

        2. PARAGRAPH NUMBERING PRESERVATION:
        - Extract paragraph numbers EXACTLY as written: [1.], [2.], [10.], [25.], etc.
        - Never modify or standardize the numbering format
        - Empty number field if no number present

        3. CONTENT HANDLING:
        - Include complete paragraph content including orders and declarations
        - When you see "orders are made" or "declarations are made", include ALL following content in that paragraph's content field
        - Use \n\n to separate distinct declarations/orders within the same paragraph
        - Example: "Accordingly the following orders are made:\n\nThe defendant breached section X\n\nThe defendant shall pay $X"

        4. QUOTED MATERIAL STRUCTURE:
        - When statutes or cases are quoted, use quoted_material field
        - Capture internal numbering like (a), (b), (i), (ii) as internal_paragraphs
        - Include source attribution (e.g., "Human Rights Act 1993, Section 21")

        5. SECTION IDENTIFICATION:
        - Common legal sections: BACKGROUND, THE LAW, THE HEARING, FINDINGS, REMEDIES
        - May have subsection headers like "Direct Discrimination" or "Indirect Discrimination"
        - Capture these as subsections within paragraphs

        6. PARTIES EXTRACTION:
        - Extract exact names as written in ALL CAPS
        - Identify roles: Plaintiff, First Defendant, Second Defendant, etc.
        - Classify type: Individual, Company, Government Agency

        7. CITATIONS CAPTURE:
        - Identify all legal references: statutes, cases, regulations
        - Categorize as: statute, case, regulation, other
        - Include context of why cited

        8. METADATA COMPLETENESS:
        - Extract ALL available metadata fields
        - Date formats as written in document
        - Page ranges for multi-case documents

        9. ERROR HANDLING:
        - If information is unclear or missing, use empty string ""
        - Never make assumptions or invent content
        - Include ALL content even if formatting seems unusual

        10. CONSISTENCY REQUIREMENTS:
            - Process ENTIRE document - never truncate or summarize
            - Maintain exact legal language and terminology
            - Preserve all technical legal references

        SCHEMA COMPLIANCE:
        Return ONLY valid JSON matching the provided schema. No additional commentary or explanation.
    """
    
    try:
        filepath = pathlib.Path(pdf_path)
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=filepath.read_bytes(),
                    mime_type='application/pdf',
                ),
                prompt
            ],
            config=generation_config
        )
        
        return response.text
    except Exception as e:
        print(f"Error processing PDF with Gemini: {e}")
        return None


def save_json_output(json_data, output_path):
    """Save extracted JSON data to file"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def process_cases():
    """Main function to process all cases"""
    cases_dir = "cases_to_process"
    json_output_dir = "json_files"
    temp_pdf_dir = "temp_pdfs"
    
    os.makedirs(json_output_dir, exist_ok=True)
    os.makedirs(temp_pdf_dir, exist_ok=True)
    
    for filename in os.listdir(cases_dir):
        file_path = os.path.join(cases_dir, filename)
        base_name = pathlib.Path(filename).stem
        
        # Skip if already processed
        output_path = os.path.join(json_output_dir, f"{base_name}.json")
        if os.path.exists(output_path):
            print(f"Skipping {filename} - already processed")
            continue
        
        if filename.endswith('.rtf'):
            print(f"Converting RTF to PDF: {filename}")
            pdf_path = convert_rtf_to_pdf(file_path, temp_pdf_dir)
            if not pdf_path:
                continue
        elif filename.endswith('.pdf'):
            pdf_path = file_path
        else:
            continue
        
        print(f"Processing with Gemini API: {filename}")
        json_response = process_pdf_with_gemini(pdf_path)
        
        if json_response:
            try:
                json_data = json.loads(json_response)
                output_path = os.path.join(json_output_dir, f"{base_name}.json")
                
                if save_json_output(json_data, output_path):
                    print(f"Successfully processed: {filename}")
                else:
                    print(f"Failed to save JSON for: {filename}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response for {filename}: {e}")
        else:
            print(f"Failed to process: {filename}")
        
        if filename.endswith('.rtf') and pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)


if __name__ == "__main__":
    process_cases()