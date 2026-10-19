# build.ps1 — real build + verification for lora-multiboot
# Builds the Heltec WiFi LoRa 32 V4 firmware with PlatformIO and runs the
# portable verification suite. Requires: PlatformIO (pio), Python 3.
param(
    [string]$Env = "heltec_v4_bridge",
    [switch]$SkipFirmware
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

try {
    Write-Host "[lora-multiboot] Verifying layout..."
    $required = @(
        "firmware/src/main.cpp",
        "firmware/src/multiboot.cpp",
        "firmware/src/SX1262Router.cpp",
        "firmware/src/WebTerminal.cpp",
        "firmware/include/multiboot.h",
        "firmware/platformio.ini",
        "firmware/partitions/quadboot.csv"
    )
    foreach ($f in $required) {
        if (-not (Test-Path $f)) { throw "Missing required file: $f" }
    }
    Write-Host "[lora-multiboot] Layout OK."

    Write-Host "[lora-multiboot] Running verification suite..."
    python tests/test_slots.py
    if ($LASTEXITCODE -ne 0) { throw "test_slots failed" }
    python tests/test_concurrent.py
    if ($LASTEXITCODE -ne 0) { throw "test_concurrent failed" }
    python tests/test_safety_bounds.py
    if ($LASTEXITCODE -ne 0) { throw "test_safety_bounds failed" }

    if (-not $SkipFirmware) {
        Write-Host "[lora-multiboot] Building firmware ($Env)..."
        Push-Location firmware
        try {
            $env:PYTHONIOENCODING = "utf-8"
            pio run -e $Env
            if ($LASTEXITCODE -ne 0) { throw "pio build failed" }
            $bin = ".pio\build\$Env\firmware.bin"
            if (-not (Test-Path $bin)) { throw "firmware.bin not produced" }
            $size = (Get-Item $bin).Length
            Write-Host ("[lora-multiboot] Firmware OK: {0} ({1:N0} bytes)" -f $bin, $size)
        }
        finally { Pop-Location }
    }

    Write-Host "[lora-multiboot] BUILD OK"
}
finally {
    Pop-Location
}
