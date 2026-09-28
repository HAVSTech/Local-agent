from pathlib import Path
import pymupdf

class DocumentAnalyzer:
    def analyze_pdf(self, path: Path) -> dict:
        doc = pymupdf.open(str(path))
        try:
            pages = []
            for page in doc:
                rect = page.rect
                orientation = "landscape" if rect.width > rect.height else "portrait"
                pages.append({"width": rect.width, "height": rect.height, "orientation": orientation})
            mixed = len({p["orientation"] for p in pages}) > 1
            return {"pages": len(pages), "mixed_orientation": mixed, "orientation": "mixed" if mixed else (pages[0]["orientation"] if pages else "portrait"), "pages_detail": pages}
        finally:
            doc.close()
