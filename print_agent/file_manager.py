from pathlib import Path
class FileManager:
    def __init__(self,allowed_roots:list[str],max_files_per_job:int=100): self.allowed_roots=[Path(p).expanduser().resolve() for p in allowed_roots]; self.max_files_per_job=max_files_per_job
    def validate_folder(self,folder:str)->Path:
        c=Path(folder).expanduser().resolve()
        if not c.exists() or not c.is_dir(): raise ValueError(f"Folder does not exist: {c}")
        for root in self.allowed_roots:
            try: c.relative_to(root); return c
            except ValueError: pass
        raise PermissionError(f"Folder is outside configured allowed roots: {c}")
    def list_files(self,folder,extensions,recursive,exclude_contains,sort_order):
        d=self.validate_folder(folder); wanted={e.lower() if e.startswith(".") else "."+e.lower() for e in extensions}; it=d.rglob("*") if recursive else d.glob("*")
        files=[p for p in it if p.is_file() and p.suffix.lower() in wanted and not any(t.lower() in p.name.lower() for t in exclude_contains)]
        files.sort(key=(lambda p:p.stat().st_mtime) if sort_order=="modified" else (lambda p:p.stat().st_ctime) if sort_order=="created" else (lambda p:p.name.lower()))
        if len(files)>self.max_files_per_job: raise RuntimeError(f"Job contains {len(files)} files; limit is {self.max_files_per_job}")
        return files
