from docx import Document
import json
from pathlib import Path
import os
from io import BytesIO

TEMPLATE_PATH = os.getenv("TEMPLATE_PATH")
templateArray =['Template Ledger.docx','Template Progress.docx','Template Transcript.docx','Template SAP.docx']
def injectTemplate(replacements,type):
    fullname = replacements["@firstName"]+replacements["@middleName"]+replacements["@lastName"]
    print(f"======== creating ledger for {fullname} =========")
    doc = Document(TEMPLATE_PATH+"/"+templateArray[type])

    # Replace in paragraphs
    for para in doc.paragraphs:
        for key, value in replacements.items():
            if key in para.text:
                para.text = para.text.replace(key, value)

    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, value)

    # Write to memory
    output_stream = BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream