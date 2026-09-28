from pathlib import Path
import time
import pymupdf
import win32con
import win32print
import win32ui
from PIL import ImageWin

PAPER_A4 = 9
PAPER_LEGAL = 5
DMDUP_SIMPLEX = 1
DMDUP_VERTICAL = 2
DMDUP_HORIZONTAL = 3

class WindowsPrintEngine:
    def __init__(self, printer_name: str, spool_wait_seconds: int = 120):
        self.printer_name = printer_name
        self.spool_wait_seconds = spool_wait_seconds

    def _get_devmode(self, paper: str, duplex: bool, edge: str, landscape: bool):
        handle = win32print.OpenPrinter(self.printer_name)
        try:
            info = win32print.GetPrinter(handle, 2)
            devmode = info["pDevMode"]
            if paper == "A4":
                devmode.PaperSize = PAPER_A4
            elif paper == "Legal":
                devmode.PaperSize = PAPER_LEGAL
            devmode.Duplex = DMDUP_SIMPLEX if not duplex else (DMDUP_HORIZONTAL if edge == "short" else DMDUP_VERTICAL)
            devmode.Orientation = win32con.DMORIENT_LANDSCAPE if landscape else win32con.DMORIENT_PORTRAIT
            devmode.Fields |= win32con.DM_PAPERSIZE | win32con.DM_DUPLEX | win32con.DM_ORIENTATION
            return devmode
        finally:
            win32print.ClosePrinter(handle)

    def _printer_dc(self, devmode):
        dc = win32ui.CreateDC()
        dc.CreateDC("WINSPOOL", self.printer_name, None, devmode)
        return dc

    def print_pdf(self, pdf_path: Path, paper: str, duplex: bool, edge: str, copies: int = 1):
        doc = pymupdf.open(str(pdf_path))
        try:
            orientations = {"landscape" if p.rect.width > p.rect.height else "portrait" for p in doc}
            if len(orientations) > 1:
                raise ValueError(f"Mixed page orientation is not supported: {pdf_path.name}")
            landscape = "landscape" in orientations
            effective_edge = edge if edge != "auto" else ("short" if landscape else "long")
            devmode = self._get_devmode(paper, duplex, effective_edge, landscape)
            dc = self._printer_dc(devmode)
            try:
                dc.SetMapMode(win32con.MM_TEXT)
                dc.StartDoc(str(pdf_path))
                for _ in range(copies):
                    for page in doc:
                        rect = page.rect
                        dc.StartPage()
                        pw = dc.GetDeviceCaps(win32con.HORZRES)
                        ph = dc.GetDeviceCaps(win32con.VERTRES)
                        scale = min(pw / rect.width, ph / rect.height)
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                        img = ImageWin.Dib(pix.tobytes("ppm"))
                        left = max(0, int((pw - pix.width) / 2))
                        top = max(0, int((ph - pix.height) / 2))
                        img.draw(dc.GetHandleOutput(), (left, top, left + pix.width, top + pix.height))
                        dc.EndPage()
                dc.EndDoc()
            finally:
                dc.DeleteDC()
        finally:
            doc.close()
        self._wait_for_queue_clear()

    def _wait_for_queue_clear(self):
        deadline = time.time() + self.spool_wait_seconds
        while time.time() < deadline:
            handle = win32print.OpenPrinter(self.printer_name)
            try:
                jobs = win32print.EnumJobs(handle, 0, 999, 1)
            finally:
                win32print.ClosePrinter(handle)
            if not jobs:
                return
            time.sleep(1)
        raise TimeoutError(f"Printer queue did not clear within {self.spool_wait_seconds} seconds")

    def printer_exists(self) -> bool:
        handle = win32print.OpenPrinter(self.printer_name)
        win32print.ClosePrinter(handle)
        return True
