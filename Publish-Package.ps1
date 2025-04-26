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
