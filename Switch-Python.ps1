# Usage: ./Switch-Python.ps1 3.12
param(
    [Parameter(Mandatory=$true)]
    [string]$PythonVersion
)

Write-Host "Switching to Python $PythonVersion"

pyenv local $PythonVersion

# Remove existing venv if it exists
if (Test-Path .venv) {
    Remove-Item -Recurse -Force .venv
}

# Create new venv with specified Python version
$pythonPath = & pyenv which python$PythonVersion
uv venv --python=$pythonPath

# Activate and install dependencies
# Using Invoke-Expression since PowerShell can't directly source like bash
if ($IsWindows) {
    & .\.venv\Scripts\Activate.ps1
} else {
    # On macOS/Linux
    & .\.venv\bin\Activate.ps1
}

uv pip install -e ".[dev]"

Write-Host "Successfully switched to Python $PythonVersion" -ForegroundColor Green
