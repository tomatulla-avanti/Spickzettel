import os

OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image

    pytesseract.get_tesseract_version()
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(path)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""
    if ext in (".txt", ".md", ".csv", ".html"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"):
        if OCR_AVAILABLE:
            try:
                return pytesseract.image_to_string(Image.open(path), lang="deu+eng")
            except Exception:
                return ""
        return ""
    return ""
