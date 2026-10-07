# CI for axiom0 (T004), PowerShell 5.1+ twin of tools/ci.sh. Run: powershell -File tools/ci.ps1
#
# For each compiler in $env:AX_CI_COMPILERS (default "gcc clang"): configure + build axiom0 with
# Ninja (warnings are errors), run the C tests (ctest), then run every optional checker that
# exists in this checkout against that build. The checkers are pre-wired so later tasks add their
# tool and never edit this script (gate tasks may):
#   tools/axtest.py --compiler <axiom0>    tools/archcheck.py
#   tools/gatecheck.py                     tools/fuzz.py --smoke
#
# Environment: AX_CI_COMPILERS, AX_CI_BUILD_TYPE (default Debug), AX_CI_BUILD_ROOT (default
#              <repo>\build-ci). Exit code: 0 everything passed, otherwise non-zero.
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Src = Join-Path $Root 'bootstrap\axiom0'
$Compilers = if ($env:AX_CI_COMPILERS) { $env:AX_CI_COMPILERS -split '\s+' } else { @('gcc', 'clang') }
$BuildType = if ($env:AX_CI_BUILD_TYPE) { $env:AX_CI_BUILD_TYPE } else { 'Debug' }
$BuildRoot = if ($env:AX_CI_BUILD_ROOT) { $env:AX_CI_BUILD_ROOT } else { Join-Path $Root 'build-ci' }

# MSYS2 ucrt64 toolchain may not be on PATH.
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    $msys = 'C:\msys64\ucrt64\bin'
    if (Test-Path (Join-Path $msys 'cmake.exe')) { $env:PATH = "$msys;$env:PATH" }
}

function Step([string]$Text) { Write-Host ""; Write-Host "== $Text" }

# Run a native command and stop on a non-zero exit code.
function Invoke-Native([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ci: FAILED ($LASTEXITCODE): $Exe $($Arguments -join ' ')"
        exit $LASTEXITCODE
    }
}

foreach ($tool in 'cmake', 'ninja') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "ci: missing tool: $tool"
        exit 127
    }
}

$Python = $null
foreach ($p in 'python', 'python3') {
    if (Get-Command $p -ErrorAction SilentlyContinue) { $Python = $p; break }
}

function Invoke-Checker([string]$Script, [string[]]$Arguments) {
    $path = Join-Path $Root "tools\$Script"
    if (-not (Test-Path $path)) {
        Write-Host "ci: tools/$Script not present, skipped"
        return
    }
    if (-not $Python) {
        Write-Host "ci: tools/$Script exists but python is not available"
        exit 127
    }
    Step "$Script $($Arguments -join ' ')"
    Push-Location $Root
    try { Invoke-Native $Python (@("tools/$Script") + $Arguments) } finally { Pop-Location }
}

foreach ($cc in $Compilers) {
    if (-not (Get-Command $cc -ErrorAction SilentlyContinue)) {
        Write-Host "ci: compiler not found: $cc"
        exit 127
    }
    $Build = Join-Path $BuildRoot $cc
    Step "configure ($cc, $BuildType)"
    Invoke-Native 'cmake' @('-S', $Src, '-B', $Build, '-G', 'Ninja', "-DCMAKE_C_COMPILER=$cc", "-DCMAKE_BUILD_TYPE=$BuildType")
    Step "build ($cc)"
    Invoke-Native 'cmake' @('--build', $Build)

    $Exe = Join-Path $Build 'axiom0.exe'
    Step "smoke: $Exe version"
    Invoke-Native $Exe @('version')

    Step "ctest ($cc)"
    Push-Location $Build
    try { Invoke-Native 'ctest' @('--output-on-failure') } finally { Pop-Location }

    Invoke-Checker 'axtest.py' @('--compiler', $Exe)
    Invoke-Checker 'archcheck.py' @()
    Invoke-Checker 'gatecheck.py' @('--compiler', $Exe)
    Invoke-Checker 'tests/gatecheck/run_selftests.py' @()
    Invoke-Checker 'fuzz.py' @('--smoke')
}

Write-Host ""
Write-Host "ci: OK ($($Compilers -join ' '))"
