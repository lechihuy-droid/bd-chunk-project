param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$InspectArgs
)

$ErrorActionPreference = "Stop"

$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $HarnessRoot
$InspectExe = Join-Path $ProjectRoot ".ih\Scripts\inspect.exe"

if (!(Test-Path $InspectExe)) {
  throw "Inspect CLI not found: $InspectExe. Run harness\install-inspect.ps1 first."
}

$LocalData = Join-Path $HarnessRoot "inspect\.localappdata"
$RoamingData = Join-Path $HarnessRoot "inspect\.appdata"
$CacheData = Join-Path $HarnessRoot "inspect\.cache"
$TraceData = Join-Path $HarnessRoot "inspect\traces"
New-Item -ItemType Directory -Force -Path $LocalData, $RoamingData, $CacheData, $TraceData | Out-Null

$env:LOCALAPPDATA = $LocalData
$env:APPDATA = $RoamingData
$env:XDG_DATA_HOME = $LocalData
$env:XDG_CACHE_HOME = $CacheData
$env:INSPECT_TRACE_FILE = Join-Path $TraceData ("trace-{0}-{1}.log" -f $PID, [guid]::NewGuid().ToString("N"))
$env:OPUS_INSPECT_DATA_DIR = $LocalData
$env:OPUS_INSPECT_CACHE_DIR = $CacheData

$SiteCustomize = Join-Path $HarnessRoot "inspect\sitecustomize"
if ($env:PYTHONPATH) {
  $env:PYTHONPATH = "$SiteCustomize;$env:PYTHONPATH"
}
else {
  $env:PYTHONPATH = $SiteCustomize
}

& $InspectExe @InspectArgs
