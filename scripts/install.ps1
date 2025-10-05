$ErrorActionPreference = "Stop"

python -m venv $env:HELM_PLUGIN_DIR\.venv
& $env:HELM_PLUGIN_DIR\.venv\Scripts\pip.exe install --upgrade pip
& $env:HELM_PLUGIN_DIR\.venv\Scripts\pip.exe install -r $env:HELM_PLUGIN_DIR\requirements.txt
