from pathlib import Path
import tempfile
from print_agent.file_manager import FileManager
from print_agent.schemas import PrintIntent

def test_allowed_root_and_filtering():
    with tempfile.TemporaryDirectory() as root:
        p=Path(root)
        (p/"a.pdf").write_text("x")
        (p/"draft.pdf").write_text("x")
        fm=FileManager([root],10)
        files=fm.list_files(root,[".pdf"],False,["draft"],"name")
        assert [x.name for x in files]==["a.pdf"]

def test_intent_limits():
    x=PrintIntent(folder="C:/x",copies=2,duplex=False,paper="A4")
    assert x.copies==2
    assert x.duplex is False
