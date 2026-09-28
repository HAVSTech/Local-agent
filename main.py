import json
from pathlib import Path
from print_agent.file_manager import FileManager
from print_agent.llm import OllamaPlanner
from print_agent.executor import PrintExecutor

def main():
    cfg=json.loads(Path("config.json").read_text(encoding="utf-8"))
    planner=OllamaPlanner(cfg["ollama_url"],cfg["model"],cfg.get("llm_timeout_seconds",120))
    fm=FileManager(cfg["allowed_roots"],cfg.get("max_files_per_job",100))
    executor=PrintExecutor(cfg["printer_name"],cfg.get("spool_wait_seconds",120))
    executor.printer.printer_exists()
    print("Local AI Print Agent")
    print("Type 'exit' to quit.")
    while True:
        command=input("Print command> ").strip()
        if command.lower() in {"exit","quit"}: break
        if not command: continue
        try:
            intent=planner.plan(command)
            if not intent.folder:
                print("Please include a usable Windows folder path.")
                continue
            files=fm.list_files(intent.folder,intent.extensions,intent.recursive,intent.exclude_contains,intent.sort_order)
            print("\nValidated plan:")
            print(intent.model_dump_json(indent=2))
            print(f"Found {len(files)} file(s).")
            for i,p in enumerate(files,1): print(f"  {i}. {p}")
            if not files:
                print("Nothing to print.")
                continue
            answer=input("Start printing? [Y/n] ").strip().lower()
            if answer not in {"","y","yes"}:
                print("Cancelled.")
                continue
            result=executor.execute(files,intent)
            print(f"Completed: {len(result['completed'])}")
            if result["failed"]:
                print(f"Stopped on failure: {result['failed'][0]}")
        except Exception as exc:
            print(f"Error: {exc}")

if __name__=="__main__": main()
