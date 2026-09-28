# Local AI Print Agent

A Windows-local AI agent that turns natural-language instructions into controlled print jobs. The LLM runs locally through Ollama; files and printer operations stay on the Windows PC.

## Current architecture
User -> Python local agent -> Ollama / Qwen3 1.7B -> validated PrintIntent -> allowed-root file manager -> PDF/Office analysis -> sequential print executor -> Brother HL-L2400D

No Vercel, Supabase, Gemini API, or cloud inference is required.

## Default print policy
- PDF: A4; one page = single-sided; multiple pages = duplex.
- PDF portrait duplex: long edge.
- PDF landscape duplex: short edge.
- Word: A4, single-sided.
- Excel: Legal, duplex, short edge.
- Files are printed sequentially. A failure stops the queue.
- The LLM cannot execute PowerShell, CMD, or arbitrary programs.
- Files must be inside configured allowed_roots.

## Supported commands
Print all PDFs in H:\Projects\Invoices
Print all PDFs in H:\Projects\Invoices double sided on A4
Print the Excel files in H:\Reports
Print the Word documents in H:\Documents
Print PDFs in H:\Invoices except files containing draft
Print PDFs in H:\Invoices sorted by modified date
Print two copies of PDFs in H:\Invoices

## Windows setup
1. Install Ollama for Windows.
2. Clone this repository.
3. Open PowerShell in the repository folder.
4. Run:
   ollama pull qwen3:1.7b
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item config.example.json config.json
5. Edit config.json: set allowed_roots and the exact Windows printer_name. Keep Ollama at http://127.0.0.1:11434.
6. Run: .\.venv\Scripts\python.exe main.py

The agent shows the interpreted plan and discovered files, then asks for confirmation before printing.

## Office documents
Word and Excel files are converted locally to temporary PDFs using Microsoft Word/Excel COM. Microsoft Office must be installed for those formats.

## Testing note
The Windows printer implementation is included, but actual driver behavior must be validated on the target Windows machine. The Brother driver is authoritative for paper sizes and duplex capabilities.

## Project structure
- main.py - local interactive agent.
- print_agent/llm.py - Ollama integration.
- print_agent/schemas.py - strict print intent model.
- print_agent/file_manager.py - allowed-root filesystem guard.
- print_agent/document_analyzer.py - PDF orientation/page analysis.
- print_agent/office_converter.py - local Office conversion.
- print_agent/print_engine.py - Windows printer DEVMODE and PDF rendering.
- print_agent/executor.py - sequential print workflow.
- tests/ - unit tests.
- docs/architecture.md - architecture details.