# run.ps1

# Define the Python executable and script paths
$pythonExecutable = "/discord-bot-hub/.venv/bin/python"
$debugpyPath = "/codespace/.vscode-remote/extensions/ms-python.debugpy-2025.8.0-linux-x64/bundled/libs/debugpy/adapter/../../debugpy/launcher"
$port = 36293
$scriptPath = "./main.py"

# Run the Python command
& $pythonExecutable $debugpyPath $port -- $scriptPath