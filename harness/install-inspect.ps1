param(
  [string]$Python = "C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe",
  [string]$VenvPath = "",
  [switch]$NoCache
)

$ErrorActionPreference = "Stop"

$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $HarnessRoot
if ($VenvPath) {
  $Venv = $VenvPath
} else {
  # Keep the venv path short on Windows. Some inspect-viz/Jupyter assets hit
  # MAX_PATH when installed under harness/.venv-inspect/.
  $Venv = Join-Path $ProjectRoot ".ih"
}
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$Req = Join-Path $HarnessRoot "requirements-inspect.txt"

if (!(Test-Path $VenvPython)) {
  & $Python -m venv $Venv
}

$pipArgs = @("-m", "pip", "install", "-U", "pip")
if ($NoCache) {
  $pipArgs += "--no-cache-dir"
}
& $VenvPython @pipArgs

$installArgs = @("-m", "pip", "install", "-r", $Req)
if ($NoCache) {
  $installArgs += "--no-cache-dir"
}
& $VenvPython @installArgs

& $VenvPython -m pip check
& (Join-Path $Venv "Scripts\inspect.exe") --version
