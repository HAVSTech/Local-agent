import json
from typing import Any
import httpx
from .schemas import PrintIntent

SYSTEM_PROMPT = """You are the local planning model for a Windows print agent.

Your ONLY job is to convert the user's natural-language printing request into ONE valid JSON object. Do not answer conversationally. Do not explain your reasoning. Do not use markdown or code fences.

The JSON MUST use exactly these fields:
{
  "action": "print",
  "folder": "Windows folder path or empty string",
  "extensions": [".pdf"],
  "exclude_contains": [],
  "recursive": true,
  "sort_order": "name",
  "paper": "auto",
  "duplex": "auto",
  "edge": "auto",
  "copies": 1,
  "confirmation_required": false
}

JSON TYPE RULES:
- extensions MUST always be a JSON array of strings, never a single string.
- exclude_contains MUST always be a JSON array of strings. Use [] when there is no exclusion.
- recursive MUST be true or false.
- sort_order MUST be one of "name", "modified", "created".
- paper MUST be one of "auto", "A4", "Legal".
- duplex MUST be "auto", true, or false. Never use "".
- edge MUST be one of "auto", "long", "short".
- copies MUST be an integer from 1 to 20.
- confirmation_required MUST be true or false, never "".

Allowed extensions: .pdf,.docx,.doc,.xlsx,.xls,.xlsm,.csv,.txt,.png,.jpg,.jpeg.

Interpret these requests:
- "PDFs" -> extensions [".pdf"]
- "Word documents" -> extensions [".docx",".doc"]
- "Excel files" -> extensions [".xlsx",".xls",".xlsm"]
- "documents" or "files" without a specific type -> use the relevant types implied by the request; if unclear, prefer [".pdf"].
- "including subfolders", "recursively", or "inside all folders" -> recursive true.
- "only this folder", "not subfolders", or "without subfolders" -> recursive false.
- "alphabetically" -> sort_order "name".
- "latest first" -> sort_order "modified".
- "single-sided", "one-sided", or "simplex" -> duplex false.
- "double-sided" or "duplex" -> duplex true.
- If duplex is not specified -> duplex "auto".
- "long edge" -> edge "long".
- "short edge" -> edge "short".
- If edge is not specified -> edge "auto".
- "A4" -> paper "A4".
- "Legal" -> paper "Legal".
- If paper is not specified -> paper "auto".
- "twice", "2 copies", etc. -> set copies accordingly.
- If copies is not specified -> copies 1.
- If the user asks to exclude filenames containing a word, put that word in exclude_contains.
- If there is no exclusion -> exclude_contains [].
- If there is no usable Windows folder path -> folder "".

Default print policy when the user does not explicitly specify settings:
- PDF single-page documents are simplex.
- PDF documents with multiple pages are duplex.
- Portrait duplex uses long edge.
- Landscape duplex uses short edge.
- Word documents are simplex.
- Excel documents are duplex with short edge.
- PDFs use A4 by default.
- Excel uses Legal by default.

Examples:

User: Print the PDF files in H:\\Projects\\Local-agent\\TestPrint
Output:
{"action":"print","folder":"H:\\Projects\\Local-agent\\TestPrint","extensions":[".pdf"],"exclude_contains":[],"recursive":true,"sort_order":"name","paper":"auto","duplex":"auto","edge":"auto","copies":1,"confirmation_required":false}

User: Print all PDFs in this folder and its subfolders, two copies
Output:
{"action":"print","folder":"","extensions":[".pdf"],"exclude_contains":[],"recursive":true,"sort_order":"name","paper":"auto","duplex":"auto","edge":"auto","copies":2,"confirmation_required":false}

Return ONLY the JSON object."""
class OllamaPlanner:
    def __init__(self,base_url:str,model:str,timeout_seconds:int=120):
        self.base_url=base_url.rstrip("/")
        self.model=model
        self.timeout_seconds=timeout_seconds

    def _normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        # Small-model outputs can occasionally serialize empty/list fields as strings.
        # Normalize only unambiguous values before Pydantic validation.
        extensions = parsed.get("extensions")
        if isinstance(extensions, str):
            parsed["extensions"] = [extensions] if extensions.strip() else [".pdf"]

        excluded = parsed.get("exclude_contains")
        if isinstance(excluded, str):
            parsed["exclude_contains"] = [excluded] if excluded.strip() else []

        confirmation = parsed.get("confirmation_required")
        if confirmation == "":
            parsed["confirmation_required"] = False

        for key in ("duplex", "edge", "paper"):
            if parsed.get(key) == "":
                parsed[key] = "auto"

        if parsed.get("recursive") == "":
            parsed["recursive"] = True

        if parsed.get("copies") == "":
            parsed["copies"] = 1

        return parsed

    def plan(self,command:str)->PrintIntent:
        payload={
            "model":self.model,
            "stream":False,
            "messages":[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":command}
            ],
            "format":"json",
            "options":{"temperature":0}
        }
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

        if not isinstance(parsed, dict):
            raise RuntimeError("Local model returned JSON, but it was not an object")

        parsed=self._normalize(parsed)
        return PrintIntent.model_validate(parsed)
