# Local AI Print Agent

Runs entirely on Windows without Vercel, Supabase, or a cloud LLM. User command -> Python agent -> Ollama/Qwen3 1.7B -> validated PrintIntent -> safe filesystem tools -> document analysis -> sequential printer engine.

The LLM never executes shell commands or receives unrestricted tools. Only configured allowed_roots may be accessed. Intended features include PDFs, Word, Excel, recursive search, exclusions, sorting, A4/Legal, simplex/duplex, long/short edge, and copies.

Prerequisites: Windows 10/11, Python 3.12+, Ollama, Qwen3 1.7B, Brother printer, and Microsoft Office for Office-to-PDF conversion.
