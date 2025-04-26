# Define the path to the .pypirc file
$pypircPath = Join-Path $HOME ".pypirc"

# Initialize credential variables
$pypiUsername = $null
$pypiPassword = $null

# Check if the .pypirc file exists
if (-not (Test-Path -Path $pypircPath -PathType Leaf)) {
    Write-Error "Error: ~/.pypirc file not found at '$pypircPath'."
    exit 1
}

Write-Host "Reading credentials from $pypircPath..."

# Read the file content and parse for [pypi] credentials
try {
    $pypircContent = Get-Content -Path $pypircPath -Raw
    # Simple parsing assuming [pypi] section and username/password lines
    if ($pypircContent -match '\[pypi\]') {
        if ($pypircContent -match '(?m)^\s*username\s*=\s*(.+)$') {
            $pypiUsername = $Matches[1].Trim()
        }
        if ($pypircContent -match '(?m)^\s*password\s*=\s*(.+)$') {
            $pypiPassword = $Matches[1].Trim()
        }
    }
} catch {
    Write-Error "Error reading or parsing '$pypircPath': $($_.Exception.Message)"
    exit 1
}

# Validate that credentials were found
if (-not $pypiUsername -or -not $pypiPassword) {
    Write-Error "Error: Could not find username and/or password under the [pypi] section in '$pypircPath'."
    exit 1
}

Write-Host "Credentials found. Username: $pypiUsername" # Username is usually __token__

# Construct and execute the uv publish command
Write-Host "Attempting to publish packages using credentials from ~/.pypirc..."
try {
    # Use Invoke-Expression if needed, but direct call is often better
    # Ensure the password is treated as a single argument, even if it contains special characters
    uv publish --username $pypiUsername --password $pypiPassword
    Write-Host "Publish command executed."
} catch {
    Write-Error "Error executing uv publish: $($_.Exception.Message)"
    exit 1
}
