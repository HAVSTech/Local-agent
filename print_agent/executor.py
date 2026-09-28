from pathlib import Path
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
            printable = source
            cleanup = False
            try:
                suffix = source.suffix.lower()
                if suffix in {".doc", ".docx", ".xls", ".xlsx", ".xlsm"}:
                    printable = self.converter.convert(source)
                    cleanup = True

                analysis = self.analyzer.analyze_pdf(printable)
                if analysis["mixed_orientation"]:
                    raise ValueError("Mixed page orientation is not supported")

                if intent.paper == "auto":
                    paper = "Legal" if suffix in {".xls", ".xlsx", ".xlsm"} else "A4"
                else:
                    paper = intent.paper

                if intent.duplex == "auto":
                    duplex = False if suffix in {".doc", ".docx"} else analysis["pages"] > 1
                    if suffix in {".xls", ".xlsx", ".xlsm"}:
                        duplex = True
                else:
                    duplex = intent.duplex

                if intent.edge == "auto":
                    if suffix in {".xls", ".xlsx", ".xlsm"}:
                        edge = "short"
                    else:
                        edge = "short" if analysis["orientation"] == "landscape" else "long"
                else:
                    edge = intent.edge

                self.printer.print_pdf(printable, paper, duplex, edge, intent.copies)
                completed.append(str(source))
            except Exception as exc:
                failed.append({"file": str(source), "error": str(exc)})
                break
            finally:
                if cleanup:
                    try:
                        printable.unlink()
                        printable.parent.rmdir()
                    except OSError:
                        pass
        return {"completed": completed, "failed": failed, "success": not failed}
