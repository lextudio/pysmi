# Development Guide for pysmi

This document outlines the common development workflows for the `pysmi` project using `uv` as the package manager.

## Setting Up Development Environment

### Create a virtual environment
```zsh
uv venv
```

### Activate the virtual environment
```zsh
source .venv/bin/activate
```

### Install the package in development mode with all dev dependencies
```zsh
uv pip install -e ".[dev]"
```

### Working with multiple Python versions

`uv` has built-in support for creating environments with specific Python versions. Here's a simpler approach:

#### Creating a virtual environment with a specific Python version

```zsh
# Specify Python version directly
uv venv --python=3.12
# Or using a pyenv-installed Python
uv venv --python=$(pyenv which python3.12)
```

#### A simple script for switching Python versions

Create a script called `Switch-Python.ps1` in your project root:

```powershell
# Usage: ./Switch-Python.ps1 3.12
param(
    [Parameter(Mandatory=$true)]
    [string]$PythonVersion
)

Write-Host "Switching to Python $PythonVersion"

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
```

Then you can simply use:
```powershell
./Switch-Python.ps1 3.12
```

Replace `3.12` with any version you need (3.9, 3.10, 3.11, 3.13).

## 1. Running Tests

### Run the entire test suite
```zsh
uv pip run pytest
```

### Run tests with coverage
```zsh
uv pip run pytest --cov=pysmi
```

### Run a specific test file
```zsh
uv pip run pytest tests/test_file.py
```

### Run tests with verbose output
```zsh
uv pip run pytest -v
```

## 2. Managing Dependencies

### List installed dependencies
```zsh
uv pip list
```

### Upgrade all dependencies
```zsh
uv pip install -e ".[dev]" --upgrade
```

### Upgrade a specific dependency
```zsh
uv pip install package_name --upgrade
```

### Add a new dependency
1. Edit `pyproject.toml` and add the dependency to the appropriate section
   - Regular dependencies under `dependencies`
   - Development dependencies under `[project.optional-dependencies].dev`
2. Install the updated dependencies:
   ```zsh
   uv pip install -e ".[dev]"
   ```

## 3. Version Management

### Bump version (patch, minor, major)
```zsh
bump2version patch  # Increments x.x.1 → x.x.2
bump2version minor  # Increments x.1.x → x.2.0
bump2version major  # Increments 1.x.x → 2.0.0
```

### Bump version without git commit/tag
```zsh
bump2version --no-commit --no-tag patch
```

## 4. Building and Publishing to PyPI

### Build the package
```zsh
uv pip install build
uv pip run python -m build
```

This will create both wheel (.whl) and source (.tar.gz) distributions in the `dist/` directory.

### Check the package
```zsh
uv pip install twine
uv pip run twine check dist/*
```

### Publish to TestPyPI (recommended for testing)
```zsh
uv pip run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

### Publish to PyPI
```zsh
uv pip run twine upload dist/*
```

### Simplified Publishing with PowerShell Script

For a Poetry-like experience, create a `Publish-Package.ps1` script:

```powershell
# Usage: ./Publish-Package.ps1 [-Test]
param(
    [switch]$Test
)

# Make sure build and twine are installed
uv pip install build twine

# Remove old dist files
if (Test-Path dist) {
    Remove-Item -Path dist -Recurse -Force
}

# Build the package
Write-Host "Building package..." -ForegroundColor Cyan
uv pip run python -m build

# Check the package
Write-Host "Checking package..." -ForegroundColor Cyan
$checkResult = uv pip run twine check dist/*
Write-Host $checkResult

# Publish the package
if ($Test) {
    Write-Host "Publishing to TestPyPI..." -ForegroundColor Yellow
    uv pip run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
} else {
    Write-Host "Publishing to PyPI..." -ForegroundColor Green
    uv pip run twine upload dist/*
}
```

Then you can simply run:

```powershell
# To publish to PyPI
./Publish-Package.ps1

# To publish to TestPyPI
./Publish-Package.ps1 -Test
```

## 5. Documentation

### Build documentation
```zsh
cd docs
uv pip run make html
```

### View documentation locally
```zsh
open docs/build/html/index.html
```

## 6. Code Quality

### Run linting checks
```zsh
uv pip run flake8 pysmi
```

### Format code with black
```zsh
uv pip run black pysmi tests
```

### Run isort to sort imports
```zsh
uv pip run isort pysmi tests
```

### Run pre-commit hooks
```zsh
uv pip run pre-commit run --all-files
```

## Complete Development Workflow Example

Here's a typical workflow for making changes:

1. Create and activate a virtual environment:
   ```zsh
   uv venv && source .venv/bin/activate
   ```

2. Install development dependencies:
   ```zsh
   uv pip install -e ".[dev]"
   ```

3. Make code changes and write tests

4. Run tests:
   ```zsh
   uv pip run pytest
   ```

5. Format and lint code:
   ```zsh
   uv pip run black pysmi tests
   uv pip run isort pysmi tests
   uv pip run flake8 pysmi
   ```

6. Bump version:
   ```zsh
   bump2version patch
   ```

7. Build and check package:
   ```zsh
   uv pip run python -m build
   uv pip run twine check dist/*
   ```

8. Publish:
   ```zsh
   uv pip run twine upload dist/*
   ```
