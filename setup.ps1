param([switch]$SkipTools, [switch]$RegisterCodex)
$ErrorActionPreference = 'Stop'
$mgsvRoot = $PSScriptRoot
$mgsvPython = Join-Path $mgsvRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $mgsvPython)) {
    uv venv (Join-Path $mgsvRoot '.venv') --python 3.11
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
uv pip install --python $mgsvPython -r (Join-Path $mgsvRoot 'requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $mgsvPython (Join-Path $mgsvRoot 'server.py') sync
if ($LASTEXITCODE -ne 0) { throw 'Wiki sync failed.' }
& $mgsvPython (Join-Path $mgsvRoot 'server.py') sync-resources
if ($LASTEXITCODE -ne 0) { Write-Warning 'Some additional sources could not refresh. Prior snapshots are retained; retry sync-resources later.' }
if (-not $SkipTools) {
    & $mgsvPython (Join-Path $mgsvRoot 'scripts\install_tools.py')
    if ($LASTEXITCODE -ne 0) { throw 'Tool installation failed.' }
}
if ($RegisterCodex) {
    codex mcp add mgsv-modding -- $mgsvPython (Join-Path $mgsvRoot 'server.py')
    if ($LASTEXITCODE -ne 0) { throw 'Codex registration failed.' }
}

# Generate a machine-local client entry; never commit this generated file.
$mgsvClient = @{ mcpServers = @{ 'mgsv-modding' = @{ command = $mgsvPython; args = @((Join-Path $mgsvRoot 'server.py')) } } }
$mgsvClientPath = Join-Path $mgsvRoot 'mcp.client.json'
[IO.File]::WriteAllText($mgsvClientPath, ($mgsvClient | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
Write-Host 'Setup complete. Machine-local client configuration: mcp.client.json'
