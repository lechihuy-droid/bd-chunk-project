param(
  [string]$Suite = "workspace-smoke",
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$HarnessArgs
)

$ErrorActionPreference = "Stop"

$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $HarnessRoot "..")
$Dockerfile = Join-Path $HarnessRoot "sandbox\Dockerfile"
$Image = "opus-agent-harness:local"

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker CLI not found. Install Docker Desktop, then rerun harness\run-docker-harness.ps1."
}

& docker build --file $Dockerfile --tag $Image $ProjectRoot.Path
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$mount = "type=bind,source=$($ProjectRoot.Path),target=/src,readonly"
$dockerArgs = @(
  "run",
  "--rm",
  "--network", "none",
  "--cpus", "2",
  "--memory", "4g",
  "--pids-limit", "256",
  "--read-only",
  "--tmpfs", "/tmp:rw,noexec,nosuid,size=512m",
  "--tmpfs", "/work:rw,nosuid,size=2g",
  "--mount", $mount,
  $Image,
  $Suite
) + $HarnessArgs

& docker @dockerArgs
