import os
import tempfile
import pytesseract
import cv2
import pandas as pd
import docx
from pdf2image import convert_from_path
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from werkzeug.utils import secure_filename

# Tesseract OCR path (for Ubuntu)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Function to extract text from an image (PNG, JPG, etc.)
def extract_text_from_image(image_path):
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return text
    except Exception as e:
        return f"Error processing image: {e}"

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        full_text = ""
        for image in images:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                img_path = temp_img.name
                image.save(img_path, 'PNG')
                full_text += extract_text_from_image(img_path)
                os.remove(img_path)
        return full_text
    except Exception as e:
        return f"Error processing PDF: {e}"

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        return f"Error processing DOCX: {e}"

# Function to extract text from an ODT file
def extract_text_from_odt(odt_path):
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w+t', encoding='utf-8') as temp_file:
            temp_txt_path = temp_file.name
            subprocess.run(['unoconv', '-f', 'txt', '-o', temp_txt_path, odt_path], check=True)
            with open(temp_txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            os.remove(temp_txt_path)
            return text
    except Exception as e:
        return f"Error processing ODT: {e}"

def index(request):
    return render(request, 'index.html')

def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        filename = secure_filename(file.name)
        file_path = os.path.join('uploads', filename)
        
        fs = FileSystemStorage()
        fs.save(file_path, file)

        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension in ['.png', '.jpg', '.jpeg']:
            extracted_text = extract_text_from_image(file_path)
        elif file_extension == '.pdf':
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            extracted_text = extract_text_from_docx(file_path)
        elif file_extension == '.odt':
            extracted_text = extract_text_from_odt(file_path)
        else:
            extracted_text = "Unsupported file type."

        os.remove(file_path)

        return render(request, 'index.html', {'extracted_text': extracted_text})

    return JsonResponse({'error': 'No file uploaded'}, status=400)

def download_file(request, format):
    text = request.POST.get('extracted_text', '')
    if not text.strip():
        return JsonResponse({'error': 'No text to save'}, status=400)
    
    # Create the file based on the chosen format
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as temp_file:
        file_path = temp_file.name
        if format == 'csv':
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
        elif format in ['xlsx', 'ods']:
            df = pd.DataFrame([line.strip() for line in text.split('\n')])
            df.to_excel(file_path, index=False, engine='odf' if format == 'ods' else 'openpyxl')
    
    return HttpResponse(file_path)
