from docx import Document
import json
from pathlib import Path
import os
from io import BytesIO

TEMPLATE_PATH = os.getenv("TEMPLATE_PATH")
templateArray =['Template Ledger.docx','Template Progress.docx','Template Transcript.docx','Template SAP.docx']

def _replace_across_runs(runs, key, value):
    """Replace key→value even if the key is split across multiple runs.
    Keeps the original run objects and their formatting."""
    if not runs:
        return

    # Build a full string and a map back to (run_idx, char_idx)
    full = []
    idx_map = []
    for ri, r in enumerate(runs):
        t = r.text or ""
        full.append(t)
        idx_map.extend([(ri, cj) for cj in range(len(t))])
    s = "".join(full)
    if not s or key not in s:
        return

    new_s = s.replace(key, value)

    # Clear all run texts (but keep the runs & formatting)
    for r in runs:
        r.text = ""

    # Re-distribute new_s back into the original runs by their original lengths
    # so formatting sticks to the same spans as much as possible.
    # Count original lengths:
    lens = []
    start = 0
    for ri, r in enumerate(runs):
        # original length of this run was how many idx_map entries had run_idx==ri
        orig_len = sum(1 for pair in idx_map if pair[0] == ri)
        lens.append(orig_len)

    pos = 0
    for ri, r in enumerate(runs):
        take = lens[ri]
        if take == 0:
            continue
        chunk = new_s[pos:pos+take]
        r.text = chunk
        pos += len(chunk)
        if pos >= len(new_s):
            break

    # If replacement made the text longer than total original chars,
    # append overflow to the last run to keep formatting.
    if pos < len(new_s):
        runs[-1].text += new_s[pos:]


def _replace_in_paragraph(paragraph, replacements: dict):
    # First, handle simple same-run replacements to avoid heavy work
    for run in paragraph.runs:
        if not run.text:
            continue
        for k, v in replacements.items():
            if k in run.text:
                run.text = run.text.replace(k, v)

    # Then handle cases where placeholders are split across runs
    for k, v in replacements.items():
        _replace_across_runs(paragraph.runs, k, v)


def _replace_in_cell(cell, replacements: dict):
    for p in cell.paragraphs:
        _replace_in_paragraph(p, replacements)
    # Recursively process nested tables too
    for t in cell.tables:
        for row in t.rows:
            for c in row.cells:
                _replace_in_cell(c, replacements)

def injectTemplate(replacements,type):
    fullname = replacements["@firstName"]+replacements["@middleName"]+replacements["@lastName"]
    print(f"======== creating template {type} for {fullname} =========")
    doc = Document(TEMPLATE_PATH+"/"+templateArray[type])

    # Replace in paragraphs
    for p in doc.paragraphs:
        _replace_in_paragraph(p, replacements)

    # Replace in cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                _replace_in_cell(cell, replacements)


    # Write to memory
    output_stream = BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream

gradeDic = {
    "A+":10,
    "A":9,
    "B":8,
    "C":7,
    "":0
}
def getFinalGrade(studentModules,studentUnits,classType):
    modules = [gradeDic[m] for m in studentModules]
    units = [gradeDic[u] for u in studentUnits]    
    
    if classType == 1:
        return sum(modules)/ 12
    
    if classType == 2:
        return sum(units) / 8
    
    if classType == 3:
        total = sum(modules) + sum(units)
        return total / 20
        
def parseFinalGrade(grade):
    if grade == 10:
        return "A+"
    
    if grade >= 9:
        return "A"
    
    if grade >=8.5:
        return "B+"
    
    if grade >=8:
        return "B"
    
    if grade >=7.5:
        return "C+"
    
    return "C"


def getGPA(grade):
    if grade >= 9:
        return 4.0
    
    if grade >= 8.5:
        return 3.33
    
    if grade >= 8:
        return 3.0
    
    if grade >= 7.5:
        return 2.33
    
    return 2.0



def getFinalGradeSAP(studentModules,studentUnits,classType):
    modules = [gradeDic[m] for m in studentModules]
    units = [gradeDic[u] for u in studentUnits]    
    
    if classType == 1:
        return sum(modules[:6])/ 6
    
    if classType == 2:
        return sum(units[:4]) / 4
    
    if classType == 3:
        total = sum(modules[:6]) + sum(units[:4])
        return total / 12
    

def insertLedgerValues(replacements,student,classObj):
    
    replacements["@ledate1"] = student.get("receiptDates")[0]
    replacements["@ledate2"] = student.get("receiptDates")[1]
    newBalance = int(classObj.total)-int(classObj.registration)
    replacements["@newb1"] = str(newBalance)

    if classObj.classType == 3: # HHA
        replacements["@pay1"] = "350"
        newBalance = newBalance - 350
        replacements["@newb2"] = str(newBalance)
        replacements["@ledate3"] = student.get("receiptDates")[2] if student.get("receiptDates")[2] else ""
        replacements["@rowV1"] = "3"
        replacements["@rowV2"] = classObj.course + " Tuition"
        replacements["@rowV3"] = "$"+str(newBalance)
        replacements["@rowV4"] = "$0"
        replacements["@rowV5"] = "$"+str(newBalance)
        replacements["@rowV6"] = "$0"
    else: 
        replacements["@pay1"] = str(newBalance)
        replacements["@newb2"] = "0"
        replacements["@ledate3"] = ""
        replacements["@rowV1"] = ""
        replacements["@rowV2"] = ""
        replacements["@rowV3"] = ""
        replacements["@rowV4"] = ""
        replacements["@rowV5"] = ""
        replacements["@rowV6"] = ""