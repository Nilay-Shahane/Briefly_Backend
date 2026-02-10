import boto3
import pdfplumber
import re
import io
import os
import hashlib


def extract_text_from_pdf(file_bytes : bytes) -> str:
    text_content = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return '\n'.join(text_content)
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
        return ""

def clean_text(text : str) -> str:
    if not text : return ''
    text = re.sub(r'\n\s*\n','||PAGE_BREAK||',text)
    text = text.replace('\n',' ')
    text = text.replace('||PAGE_BREAK||','\n\n')
    text = re.sub(r'[ \t]+',' ',text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def process_pdf(file_bytes : bytes )->str:
    raw_text = extract_text_from_pdf(file_bytes)
    cleaned_text = clean_text(raw_text)
    return cleaned_text
