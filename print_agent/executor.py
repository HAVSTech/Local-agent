from pathlib import Path
import tempfile
from .document_analyzer import DocumentAnalyzer
from .office_converter import OfficeConverter
from .print_engine import WindowsPrintEngine
from .schemas import PrintIntent

class PrintExecutor:
    def __init__(self, printer_name: str, spool_wait_seconds: int):
        self.analyzer = DocumentAnalyzer()
        self.converter = OfficeConverter()
        self.printer = WindowsPrintEngine(printer_name, spool_wait_seconds)

    def execute(self, files: list[Path], intent: PrintIntent) -> dict:
        completed = []
        failed = []
        for source in files:
            try:
                printable = source
                cleanup = False
                if source.suffix.lower() in {".doc", ".docx", ".xls", ".xlsx", ".xlsm"}:
                    printable = self.converter.convert(source)
                    cleanup = True

                if printable.suffix.lower() == ".pdf":
                    analysis = self.analyzer.analyze_pdf(printable)
                    if analysis["mixed_orientation"]:
                        raise ValueError("Mixed page orientation is not supported")

                paper = intent.paper
                if paper == "auto":
                    paper = "Legal" if source.suffix.lower() in {".xls", ".xlsx", ".xlsm"} else "A4"
                duplex = intent.duplex
                edge = intent.edge
                if edge == "auto" and source.suffix.lower() in {".xls", ".xlsx", ".xlsm"}:
                    edge = "short"
                elif edge == "auto":
                    edge = "long"

                self.printer.print_pdf(printable, paper, duplex, edge, intent.copies)
                completed.append(str(source))
                if cleanup:
                    try:
                        printable.unlink()
                        printable.parent.rmdir()
                    except OSError:
                        pass
            except Exception as exc:
                failed.append({"file": str(source), "error": str(exc)})
                break
        return {"completed": completed, "failed": failed, "success": not failed}
