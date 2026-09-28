from pathlib import Path
import tempfile
import pythoncom
import win32com.client

class OfficeConverter:
    def convert(self, source: Path) -> Path:
        suffix = source.suffix.lower()
        if suffix in {".doc", ".docx"}:
            return self._word(source)
        if suffix in {".xls", ".xlsx", ".xlsm"}:
            return self._excel(source)
        raise ValueError(f"Unsupported Office file: {source}")

    def _word(self, source: Path) -> Path:
        pythoncom.CoInitialize()
        app = None
        try:
            app = win32com.client.DispatchEx("Word.Application")
            app.Visible = False
            doc = app.Documents.Open(str(source), ReadOnly=True)
            out = Path(tempfile.mkdtemp(prefix="local_print_")) / f"{source.stem}.pdf"
            doc.ExportAsFixedFormat(str(out), 17)
            doc.Close(False)
            return out
        finally:
            if app is not None:
                app.Quit()
            pythoncom.CoUninitialize()

    def _excel(self, source: Path) -> Path:
        pythoncom.CoInitialize()
        app = None
        try:
            app = win32com.client.DispatchEx("Excel.Application")
            app.Visible = False
            book = app.Workbooks.Open(str(source), ReadOnly=True)
            out = Path(tempfile.mkdtemp(prefix="local_print_")) / f"{source.stem}.pdf"
            book.ExportAsFixedFormat(0, str(out))
            book.Close(False)
            return out
        finally:
            if app is not None:
                app.Quit()
            pythoncom.CoUninitialize()
