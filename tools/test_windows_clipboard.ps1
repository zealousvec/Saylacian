param(
# Exercises actual Windows clipboard copy and restore behavior for Saylacian.
    [string]$Project = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidencePath = (Join-Path $env:USERPROFILE 'Downloads\Saylacian-Safety-Backups\windows-clipboard-acceptance')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
New-Item -ItemType Directory -Force -Path $EvidencePath | Out-Null
$before = [System.Windows.Forms.Clipboard]::GetDataObject()
$savedText = $null
$beforeFormats = @()
if ($null -ne $before) {
    $beforeFormats = @($before.GetFormats($false))
    $nonText = @($beforeFormats | Where-Object {
        $_ -notin @('UnicodeText', 'Locale', 'Text', 'OEMText', 'System.String')
    })
    if ($nonText.Count -gt 0) {
        throw "Refusing to replace clipboard with non-text formats: $($nonText -join ', ')"
    }
    if ([System.Windows.Forms.Clipboard]::ContainsText()) {
        $savedText = [System.Windows.Forms.Clipboard]::GetText()
    }
}

$python = Join-Path $Project '.venv\Scripts\python.exe'
$writer = Join-Path $Project 'tools\clipboard_payload_writer.py'
$reader = Join-Path $Project 'tools\read_windows_clipboard.ps1'
$pwsh = Join-Path $PSHOME 'pwsh.exe'
$sample = 'hello, what is wrong with you,'
$report = [System.Collections.Generic.List[object]]::new()

try {
    foreach ($mode in @('latin', 'image', 'saylacian')) {
        $requestPath = Join-Path $EvidencePath "request-$mode.json"
        $writerResult = Join-Path $EvidencePath "writer-$mode.json"
        $readerEvidence = Join-Path $EvidencePath "reader-$mode.json"
        $imagePath = Join-Path $EvidencePath 'image-from-external-reader.png'
        $request = @{ mode = $mode; script = 'Borama'; text = $sample; result_path = $writerResult }
        $request | ConvertTo-Json | Set-Content -LiteralPath $requestPath -Encoding utf8
        & $python $writer --input-json $requestPath
        if ($LASTEXITCODE -ne 0) { throw "Clipboard writer failed for $mode." }

        & $pwsh -NoLogo -NoProfile -Sta -File $reader `
            -Mode $mode -EvidencePath $readerEvidence -ImagePath $imagePath
        if ($LASTEXITCODE -ne 0) { throw "Separate WinForms reader failed for ${mode}." }
        $externalJson = Get-Content -LiteralPath $readerEvidence -Raw | ConvertFrom-Json
        if ($mode -eq 'saylacian') {
            $verify = Join-Path $Project 'tools\verify_saylacian_clipboard.py'
            & $python $verify --reader-evidence $readerEvidence --expected-latin $sample --script Borama
            if ($LASTEXITCODE -ne 0) { throw 'Clipboard Saylacian Text did not round-trip from the external WinForms reader.' }
        }
        if ($mode -eq 'image') {
            Move-Item -LiteralPath $imagePath -Destination (Join-Path $EvidencePath 'copied-borama.png') -Force
            $externalJson.image_saved = Join-Path $EvidencePath 'copied-borama.png'
        }
        $report.Add([pscustomobject]@{
            mode = $mode
            writer = (Get-Content -LiteralPath $writerResult -Raw | ConvertFrom-Json)
            external_reader = $externalJson
        })
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $EvidencePath 'windows-clipboard-results.json') -Encoding utf8
    Write-Output 'Windows clipboard + separate WinForms reader: PASS for Latin, image, and Saylacian Text formats.'
}
finally {
    [System.Windows.Forms.Clipboard]::Clear()
    if ($null -ne $savedText) { [System.Windows.Forms.Clipboard]::SetText($savedText) }
}
