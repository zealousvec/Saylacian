param(
    [string]$Python,
    [switch]$SkipPackage,
    [string]$PackageIdentity,
    [string]$Publisher,
    [string]$PublisherDisplayName,
    [string]$Version = '0.1.0.0',
    [string]$MakeAppx
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = Join-Path $repo '.venv\Scripts\python.exe'
}
$Python = (Resolve-Path $Python).Path
Set-Location $repo

if (-not (Test-Path (Join-Path $repo 'requirements-runtime-lock.txt'))) {
    throw 'Run this script from a complete Saylacian source checkout.'
}

& $Python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12 for release builds'; import PyInstaller; assert PyInstaller.__version__ == '6.22.3', 'Install the pinned packaging requirements'"
if ($LASTEXITCODE -ne 0) { throw 'Build environment check failed.' }
& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Build environment has inconsistent dependencies.' }

$buildRoot = Join-Path $repo 'build\windows'
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
$env:KIVY_HOME = Join-Path $buildRoot 'kivy'
$env:KIVY_NO_CONSOLELOG = '1'
$env:KIVY_NO_ARGS = '1'
$licenseData = "$repo\LICENSE;."

$pyinstallerArgs = @(
    '-m', 'PyInstaller', '--clean', '--noconfirm', '--onedir', '--windowed',
    '--log-level', 'WARN', '--name', 'Saylacian', '--contents-directory', '_internal',
    '--specpath', (Join-Path $buildRoot 'spec'),
    '--distpath', (Join-Path $buildRoot 'dist'),
    '--workpath', (Join-Path $buildRoot 'work'),
    '--add-data', "$repo\app;app",
    '--add-data', "$repo\assets;assets",
    '--add-data', "$repo\notices;notices",
    '--add-data', $licenseData,
    '--add-data', "$repo\THIRD_PARTY_NOTICES.md;.",
    '--add-data', "$repo\saylacian\core\data;saylacian/core/data",
    '--collect-data', 'py3langid',
    '--collect-binaries', 'ctranslate2',
    '--hidden-import', 'ctranslate2',
    '--hidden-import', 'sentencepiece',
    '--hidden-import', 'onnxruntime',
    '--hidden-import', 'tokenizers',
    '--hidden-import', 'py3langid.langid',
    'main.py'
)
& $Python @pyinstallerArgs
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

$dist = Join-Path $buildRoot 'dist\Saylacian'
& $Python (Join-Path $repo 'tools\package_windows.py') verify --dist-dir $dist
if ($LASTEXITCODE -ne 0) { throw 'Packaged app payload verification failed.' }

if (-not $SkipPackage) {
    if ([string]::IsNullOrWhiteSpace($PackageIdentity) -or [string]::IsNullOrWhiteSpace($Publisher) -or [string]::IsNullOrWhiteSpace($PublisherDisplayName)) {
        throw 'Supply the exact package identity and publisher values from Partner Center, or use -SkipPackage for a local app build.'
    }
    if ([string]::IsNullOrWhiteSpace($MakeAppx)) {
        throw 'Supply the signed Windows SDK MakeAppx.exe path with -MakeAppx.'
    }
    $packagePath = Join-Path $buildRoot "store\Saylacian-$Version-x64.msix"
    & $Python (Join-Path $repo 'tools\package_windows.py') package `
        --dist-dir $dist `
        --makeappx $MakeAppx `
        --output $packagePath `
        --identity $PackageIdentity `
        --publisher $Publisher `
        --publisher-display-name $PublisherDisplayName `
        --version $Version
    if ($LASTEXITCODE -ne 0) { throw 'MSIX package creation failed.' }
}

Write-Output "Windows build completed: $dist"
