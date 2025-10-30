import base64, io
from pdf2image import convert_from_bytes

def pdf_to_page_images(pdf_bytes: bytes, dpi, max_pages):
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)  # needs poppler
    if max_pages: pages = pages[:max_pages]
    data_urls = []
    for im in pages:
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_urls.append(f"data:image/jpeg;base64,{b64}")
    return data_urls