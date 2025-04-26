# Run-Tests.ps1
# A script to run tests for pysmi project
param(
    [switch]$Coverage,      # Run with coverage report
    [switch]$Verbose,       # Run with verbose output
    [string]$TestFile = "", # Specific test file to run
    [string]$TestPath = "tests", # Path to test directory
    [string]$Args = ""      # Additional pytest arguments
)

# Check if virtual environment is active
if (-not (Test-Path ".venv")) {
    Write-Host "No virtual environment found. Creating one..." -ForegroundColor Yellow
    uv venv
    if ($IsWindows) {
        & .\.venv\Scripts\Activate.ps1
    } else {
        # On macOS/Linux
        & .\.venv\bin\Activate.ps1
    }
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    uv pip install -e ".[dev]"
}

Write-Host "Running tests for pysmi..." -ForegroundColor Cyan

# Build the command
$command = "uv run pytest"

if ($Verbose) {
    $command += " -v"
}

if ($Coverage) {
    $command += " --cov=pysmi --cov-report=term --cov-report=html"
}

if ($TestFile -ne "") {
    $command += " $TestFile"
} else {
    $command += " $TestPath"
}

if ($Args -ne "") {
    $command += " $Args"
}

# Display the command being run
Write-Host "Executing: $command" -ForegroundColor DarkGray

# Run the command
Invoke-Expression $command

# Open coverage report if generated
if ($Coverage) {
    Write-Host "`nCoverage report generated in htmlcov/index.html" -ForegroundColor Green

    if ($IsWindows) {
        Start-Process "htmlcov\index.html"
    } elseif ($IsMacOS) {
        Start-Process "open" -ArgumentList "htmlcov/index.html"
    } elseif ($IsLinux) {
        Start-Process "xdg-open" -ArgumentList "htmlcov/index.html"
    }
}
