$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$python = Join-Path $root ".ih\Scripts\python.exe"
$server = Join-Path $root "harness\hub\server.py"

& $python $server
