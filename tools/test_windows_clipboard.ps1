# SPDX-License-Identifier: AGPL-3.0-or-later
# Verifies clipboard formats inside a disposable Windows VM.

param(
    [string]$Project = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidencePath = (
        Join-Path $env:TEMP 'Saylacian-windows-clipboard-acceptance'
    ),
    [Parameter(Mandatory = $true)]
    [switch]$InDisposableWindowsVm
)

$ErrorActionPreference = 'Stop'

if (
    -not $InDisposableWindowsVm -or
    $env:SAYLACIAN_CLIPBOARD_TEST_ENV -ne 'disposable-vm'
) {
    throw (
        'Run only inside a disposable Windows VM with host clipboard sharing ' +
        'disabled. Pass -InDisposableWindowsVm and set ' +
        'SAYLACIAN_CLIPBOARD_TEST_ENV=disposable-vm there.'
    )
}

Add-Type -AssemblyName System.Windows.Forms
$before = [System.Windows.Forms.Clipboard]::GetDataObject()
if ($null -ne $before -and @($before.GetFormats($false)).Count -gt 0) {
    throw 'Refusing to modify a non-empty clipboard. Reset the disposable VM first.'
}

New-Item -ItemType Directory -Force -Path $EvidencePath | Out-Null

$python = Join-Path $Project '.venv\Scripts\python.exe'
$writer = Join-Path $Project 'tools\clipboard_payload_writer.py'
$reader = Join-Path $Project 'tools\read_windows_clipboard.ps1'
$pwsh = Join-Path $PSHOME 'pwsh.exe'
$sample = 'hello, what is wrong with you,'
$report = [System.Collections.Generic.List[object]]::new()

foreach ($mode in @('latin', 'image', 'saylacian')) {
    $requestPath = Join-Path $EvidencePath "request-$mode.json"
    $writerResult = Join-Path $EvidencePath "writer-$mode.json"
    $readerEvidence = Join-Path $EvidencePath "reader-$mode.json"
    $imagePath = Join-Path $EvidencePath 'image-from-external-reader.png'
    $request = @{
        mode       = $mode
        script     = 'Borama'
        text       = $sample
        result_path = $writerResult
    }
    $request | ConvertTo-Json | Set-Content -LiteralPath $requestPath -Encoding utf8

    & $python $writer --input-json $requestPath
    if ($LASTEXITCODE -ne 0) {
        throw "Clipboard writer failed for $mode."
    }

    $readerParameters = @{
        Mode         = $mode
        EvidencePath = $readerEvidence
        ImagePath    = $imagePath
    }
    & $pwsh -NoLogo -NoProfile -Sta -File $reader @readerParameters
    if ($LASTEXITCODE -ne 0) {
        throw "Separate WinForms reader failed for $mode."
    }

    $externalJson = Get-Content -LiteralPath $readerEvidence -Raw | ConvertFrom-Json
    if ($mode -eq 'saylacian') {
        $verify = Join-Path $Project 'tools\verify_saylacian_clipboard.py'
        & $python $verify `
            --reader-evidence $readerEvidence `
            --expected-latin $sample `
            --script Borama

        if ($LASTEXITCODE -ne 0) {
            throw (
                'Clipboard Saylacian Text did not round-trip from the ' +
                'external WinForms reader.'
            )
        }
    }

    if ($mode -eq 'image') {
        $savedImage = Join-Path $EvidencePath 'copied-borama.png'
        Move-Item -LiteralPath $imagePath -Destination $savedImage -Force
        $externalJson.image_saved = $savedImage
    }

    $writerJson = Get-Content -LiteralPath $writerResult -Raw | ConvertFrom-Json
    $report.Add(
        [pscustomobject]@{
            mode            = $mode
            writer          = $writerJson
            external_reader = $externalJson
        }
    )
}

$reportPath = Join-Path $EvidencePath 'windows-clipboard-results.json'
$report |
    ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $reportPath -Encoding utf8

Write-Output 'Windows clipboard + separate WinForms reader: PASS for Latin, image, and Saylacian Text formats.'
