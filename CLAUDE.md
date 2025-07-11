This project iterates over legal cases, in the cases_to_process_folder, first to json files following the legal_case_schema.json, which are saved to json_files folder, then the json file is converted to a md file pursuant to the json_to_pdf.py file which is then saved to markdown_output. 

The code is minimal, there are no tests, no progresses, etc. 

The gemini_api.py file does the following:
1. Iterates through all the legal cases in cases_to_process
2. If the item is a rtf, it converts it to a pdf using libreoffice
3. If the item is a pdf, it begins the process
4. The process calls the gemini api with the PDF to create a json structured output following the legal_case_schema.json exactly
5. Saves the extracted JSON data to json_files folder

Requirements:
- google-genai Python package must be installed (pip install google-genai)
- spire.doc Python package must be installed (pip install spire.doc)

Implementation Details:
- API key: AIzaSyCfzbxC8NFcgq0Jpl6ZIyeztwSh1VSRU7A (hardcoded in gemini_api.py)
- Model: gemini-2.5-pro
- Uses Google GenAI SDK with JSON schema validation
- RTF files are converted to PDF using Spire.Doc before processing
- Generated JSON follows legal_case_schema.json structure exactly
- Temporary PDF files are cleaned up after processing

