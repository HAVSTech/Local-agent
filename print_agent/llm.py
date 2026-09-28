import json
from typing import Any
import httpx
from .schemas import PrintIntent

SYSTEM_PROMPT = """You are the local planning model for a Windows print agent. Convert a user printing request into ONLY valid JSON with fields action, folder, extensions, exclude_contains, recursive, sort_order, paper, duplex, edge, copies, confirmation_required. Never execute commands, invent files, or access the filesystem.
Allowed extensions: .pdf,.docx,.doc,.xlsx,.xls,.xlsm,.csv,.txt,.png,.jpg,.jpeg.
paper: auto,A4,Legal. edge: auto,long,short. duplex: auto,true,false. sort_order: name,modified,created.
If the user explicitly says single-sided/one-sided/simplex, use false. If explicitly double-sided/duplex, use true. If not specified, use auto.
Default print policy: PDF single-page documents become simplex; PDF documents with multiple pages become duplex; Word documents are simplex; Excel documents are duplex with short edge; PDFs use A4 by default; Excel uses Legal by default.
If there is no usable Windows folder path, set folder to empty string."""
class OllamaPlanner:
    def __init__(self,base_url:str,model:str,timeout_seconds:int=120):
        self.base_url=base_url.rstrip("/")
        self.model=model
        self.timeout_seconds=timeout_seconds
    def plan(self,command:str)->PrintIntent:
        payload={"model":self.model,"stream":False,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":command}],"format":"json","options":{"temperature":0}}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            r=client.post(f"{self.base_url}/api/chat",json=payload)
            r.raise_for_status()
            data:dict[str,Any]=r.json()
        content=data.get("message",{}).get("content","")
        if not content:
            raise RuntimeError("Ollama returned an empty response")
        try:
            parsed=json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Local model returned invalid JSON") from exc
        return PrintIntent.model_validate(parsed)
