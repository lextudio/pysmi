# Check if the dist directory exists and remove it
if (Test-Path -Path "dist" -PathType Container) {
    Write-Host "Removing existing dist directory..."
    Remove-Item -Recurse -Force "dist"
} else {
    Write-Host "dist directory not found. Skipping removal."
}

# Build the packages
Write-Host "Building packages..."
uv build

Write-Host "Build process completed."
