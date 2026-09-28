# Local AI Print Agent

A Windows-local AI print agent for natural-language printing commands.

## Architecture

User command -> Local Agent -> Ollama/Qwen3 -> Structured print intent -> Safety validation -> File discovery -> Document analysis -> Print queue -> Windows printer.

The agent is designed to run entirely on the Windows machine. No Vercel, Supabase, or cloud LLM is required.

## Planned runtime

- Python 3.12+
- Windows 10/11
- Ollama
- Qwen3 1.7B
- PyMuPDF
- pywin32
- Pillow
- Optional Microsoft Word/Excel for Office conversion

## Safety

The LLM never executes arbitrary shell commands. It produces a restricted JSON print intent that is validated before any filesystem or printer action.

See `docs/architecture.md` for the implementation plan.
