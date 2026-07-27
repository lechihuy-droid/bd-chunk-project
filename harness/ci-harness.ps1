param(
  [switch]$SkipInspect
)

$ErrorActionPreference = "Stop"

$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $HarnessRoot "..")
$Py311 = "C:\Users\HUY\AppData\Local\Programs\Python\Python311\python.exe"
$InspectPython = Join-Path $ProjectRoot ".ih\Scripts\python.exe"

if (!(Test-Path $Py311)) {
  $Py311 = "python"
}

Push-Location $ProjectRoot
try {
  & $Py311 "harness\run_harness.py" --suite workspace-smoke
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  & $Py311 "harness\run_harness.py" --suite boundary-compliance
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  if ($SkipInspect) {
    exit 0
  }

  $tasks = @(
    "harness\inspect\tasks\workspace_smoke.py",
    "harness\inspect\tasks\boundary_compliance.py"
  )

  foreach ($task in $tasks) {
    & "harness\run-inspect.ps1" eval $task --log-dir "harness\inspect\logs" --display plain
    if ($LASTEXITCODE -ne 0) {
      if (Test-Path $InspectPython) {
        & $InspectPython "harness\inspect\export_mep.py"
      }
      exit $LASTEXITCODE
    }
  }
}
finally {
  Pop-Location
}
