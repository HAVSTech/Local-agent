$ErrorActionPreference="Stop"
ollama --version
ollama pull qwen3:1.7b
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if(-not(Test-Path "config.json")){Copy-Item "config.example.json" "config.json";Write-Host "Edit config.json before running."}
